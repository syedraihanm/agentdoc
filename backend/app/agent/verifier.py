import re
import ast
import unicodedata
from typing import Any
from backend.app.config import settings
from backend.app.agent.schemas import Answer, VerifiedAnswer
from backend.app.agent.injection import INJECTION_PATTERNS

# Only high-precision patterns may veto an answer. Patterns 3 ("respond with") and
# 4 ("never use") are common in legitimate policy text and caused false positives.
ANSWER_ECHO_PATTERNS = [INJECTION_PATTERNS[i] for i in (0, 1, 2, 5, 6)]

CHAR_MAP = {
    '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
    '\u2013': '-', '\u2014': '-', '\u2212': '-', '\u00ad': ''
}

def normalize_for_quote_match(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize('NFKC', text)
    for k, v in CHAR_MAP.items():
        s = s.replace(k, v)
    # De-hyphenate linebreaks
    s = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', s)
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s

def safe_eval_expression(expr: str) -> float | int | None:
    """Safe arithmetic evaluator: digits, +, -, *, /, (, ) only."""
    if not re.match(r'^[0-9\.\s\+\-\*\/\(\)]+$', expr):
        return None
    try:
        tree = ast.parse(expr, mode='eval')
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                if isinstance(node.op, ast.Add): return left + right
                if isinstance(node.op, ast.Sub): return left - right
                if isinstance(node.op, ast.Mult): return left * right
                if isinstance(node.op, ast.Div): return left / right if right != 0 else None
            return None
        return _eval(tree)
    except Exception:
        return None

def extract_numeric_tokens(text: str) -> list[str]:
    # Extract numbers, percentages, currencies e.g. $1,500, 60, 4 days
    raw = re.findall(r'[$€£¥]?\b\d+(?:,\d+)*(?:\.\d+)?\b%?', text)
    cleaned = []
    for r in raw:
        num_only = re.sub(r'[$€£¥,]', '', r)
        cleaned.append(num_only)
    return cleaned

def verify_answer(
    answer: Answer,
    fetched_pages: dict[int, str],
    user_question: str,
    ledger_signals: dict[str, Any] | None = None
) -> VerifiedAnswer:
    ver_details: dict[str, Any] = {
        "v1_quotes_checked": 0,
        "v1_quotes_valid": 0,
        "dropped_quotes": [],
        "numeric_passed": True,
        "injection_cleared": True,
        "original_status": answer.status,
        "final_status": answer.status,
        "downgrade_reason": None,
        "warnings": []
    }

    # Pre-normalize fetched pages supporting both int and (doc_id, page) keys
    norm_pages_by_doc_page: dict[tuple[str, int], str] = {}
    norm_pages_by_page: dict[int, str] = {}
    for k, txt in fetched_pages.items():
        norm_txt = normalize_for_quote_match(txt)
        if isinstance(k, tuple):
            did, p = k
            norm_pages_by_doc_page[(str(did), int(p))] = norm_txt
            norm_pages_by_page[int(p)] = norm_txt
        else:
            p = int(k)
            norm_pages_by_page[p] = norm_txt

    def get_norm_text_for_item(p_num: int, did: str | None) -> tuple[str | None, str]:
        if did:
            if (str(did), p_num) in norm_pages_by_doc_page:
                return norm_pages_by_doc_page[(str(did), p_num)], "ok"
            # Explicit doc_id specified but page not read from that document
            return None, "doc_page_not_read"
        if p_num in norm_pages_by_page:
            return norm_pages_by_page[p_num], "ok"
        return None, "page_not_read"

    # V1 & V2: Verify Evidence Quotes
    valid_evidence = []
    for item in answer.evidence:
        ver_details["v1_quotes_checked"] += 1
        page_num = item.page
        item_doc = getattr(item, "doc_id", None)
        target_norm, reason = get_norm_text_for_item(page_num, item_doc)
        if target_norm is None:
            ver_details["dropped_quotes"].append({"doc_id": item_doc, "page": page_num, "quote": item.quote, "reason": reason})
            continue
        
        norm_quote = normalize_for_quote_match(item.quote)
        if norm_quote and norm_quote in target_norm:
            valid_evidence.append(item)
            ver_details["v1_quotes_valid"] += 1
        else:
            ver_details["dropped_quotes"].append({"doc_id": item_doc, "page": page_num, "quote": item.quote, "reason": "quote_not_found_on_page"})

    # V1 & V2: Verify Conflict Quotes
    valid_conflicts = []
    for conf in answer.conflicts:
        ch = conf.chosen
        sup_list = conf.superseded
        ch_text, _ = get_norm_text_for_item(ch.page, getattr(ch, "doc_id", None))
        ch_ok = (ch_text is not None and normalize_for_quote_match(ch.quote) in ch_text)
        valid_sup = []
        for s in sup_list:
            s_text, _ = get_norm_text_for_item(s.page, getattr(s, "doc_id", None))
            if s_text is not None and normalize_for_quote_match(s.quote) in s_text:
                valid_sup.append(s)
        if ch_ok:
            conf.superseded = valid_sup
            valid_conflicts.append(conf)

    answer.evidence = valid_evidence
    answer.conflicts = valid_conflicts

    # V3: Non-empty support check
    if answer.status in ("answered", "partial") and len(valid_evidence) == 0:
        answer.status = "insufficient"
        ver_details["final_status"] = "insufficient"
        ver_details["downgrade_reason"] = "No quotes could be verified against read pages."
        answer.answer = "The document does not contain sufficient verified information to answer this question."

    # V4: Strict Numeric Verification
    if settings.STRICT_NUMERIC_VERIFY and answer.status != "insufficient":
        calc_res = None
        if answer.calculation:
            calc_res = safe_eval_expression(answer.calculation.expression)
            if calc_res is not None:
                answer.calculation.result = calc_res

        evidence_text = " ".join([e.quote for e in valid_evidence])
        conflict_text = " ".join([c.chosen.quote + " " + " ".join([s.quote for s in c.superseded]) for c in valid_conflicts])
        all_read_pages_text = " ".join(fetched_pages.values())
        heading_text = " ".join([h.get("title", "") for h in (ledger_signals or {}).get("headings", [])])
        read_page_nums = [str(p) for p in norm_pages_by_page.keys()]
        allowed_nums = set(
            extract_numeric_tokens(evidence_text) +
            extract_numeric_tokens(conflict_text) +
            extract_numeric_tokens(all_read_pages_text) +
            extract_numeric_tokens(heading_text) +
            extract_numeric_tokens(user_question) +
            read_page_nums
        )
        if calc_res is not None:
            allowed_nums.add(str(calc_res))

        answer_nums = extract_numeric_tokens(answer.answer)
        unverified_nums = [n for n in answer_nums if n not in allowed_nums]
        if unverified_nums:
            ver_details["numeric_passed"] = False
            ver_details["warnings"].append(f"Unverified figures in answer: {unverified_nums}")
            # If evidence exists, downgrade to partial; else insufficient
            if answer.status == "answered":
                answer.status = "partial"
                ver_details["final_status"] = "partial"
                ver_details["downgrade_reason"] = f"Figures {unverified_nums} could not be traced to verified quotes."

    # V5: Injection Echo
    for ignored in answer.ignored_instructions:
        if ignored.excerpt and ignored.excerpt.lower() in answer.answer.lower():
            answer.answer = re.sub(re.escape(ignored.excerpt), "[IGNORED_INJECTION]", answer.answer, flags=re.IGNORECASE)
            ver_details["injection_cleared"] = False

    for pat in ANSWER_ECHO_PATTERNS:
        if pat.search(answer.answer) and not pat.search(user_question):
            ver_details["injection_cleared"] = False
            answer.status = "insufficient"
            ver_details["final_status"] = "insufficient"
            answer.answer = "The document does not contain verifiable instructions to answer this question."
            ver_details["downgrade_reason"] = "Detected potential prompt injection echo in proposed answer."

    # V7: Status consistency
    if answer.status == "insufficient":
        if not answer.answer.strip():
            answer.answer = "The document does not contain enough information to answer this."
    elif answer.status == "answered":
        answer.not_found = []

    return VerifiedAnswer(answer_obj=answer, verification=ver_details)