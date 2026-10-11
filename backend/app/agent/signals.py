import re
from typing import Any

AMENDMENT_HEADING_REGEX = re.compile(
    r'\b(amend|addend|errata|erratum|corrigend|revision|change log|changes|supplement|update|supersed|notice|bulletin|clarification|exhibit|schedule|appendix|annex)\b',
    re.IGNORECASE
)

CROSS_REF_REGEX = re.compile(
    r'\b(see\s+(section|clause|article|appendix|annex|exhibit|table|figure|page)\s+([A-Za-z0-9\.\-]+)|as\s+(amended|modified|revised)|subject\s+to|notwithstanding|except\s+as|supersede[sd]?|replaces|in\s+lieu\s+of|effective\s+(from|as\s+of|on)\s+([A-Za-z0-9\-\/]+)|no\s+longer|hereby\s+amended)\b',
    re.IGNORECASE
)

DATE_REGEX = re.compile(
    r'\b(20\d\d[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])|(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d\d)\b',
    re.IGNORECASE
)

def find_amendment_headings(headings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for h in headings:
        title = h.get("title", "")
        if AMENDMENT_HEADING_REGEX.search(title):
            results.append({"title": title, "page": h.get("page", 1)})
    return results

def find_cross_references(page_text: str, headings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs = []
    for match in CROSS_REF_REGEX.finditer(page_text):
        phrase = match.group(0).strip()
        target_page = None
        
        # Check if phrase explicitly gives a page or section number
        # e.g., "see page 9", "see Section 4", "Appendix A"
        for h in headings:
            htitle = h.get("title", "").lower()
            # If heading contains the matched target like "section 4" or "appendix a"
            words = phrase.lower().split()
            if len(words) >= 2:
                key = " ".join(words[-2:])
                if key in htitle:
                    target_page = h.get("page")
                    break
        refs.append({
            "phrase": phrase,
            "resolved_page": target_page
        })
    return refs

def find_dates(page_text: str) -> list[str]:
    return [m.group(0) for m in DATE_REGEX.finditer(page_text)]

def partition_unread_hits(all_hits: set[int], read_pages: set[int]) -> dict[str, list[int]]:
    unread = sorted(list(all_hits - read_pages))
    if not read_pages:
        return {"before_last_read": [], "after_last_read": unread}
    last_read = max(read_pages)
    return {
        "before_last_read": [p for p in unread if p < last_read],
        "after_last_read": [p for p in unread if p > last_read]
    }