import re
from collections import Counter
import pymupdf

NUMBERING_REGEX = re.compile(r'^(\d+(\.\d+){0,3})[.)]?\s+\S')
KEYWORDS_REGEX = re.compile(r'^(Article|Section|Chapter|Part|Appendix|Annex|Annexure|Schedule|Exhibit|Amendment|Addendum|Errata)\b', re.IGNORECASE)
DOT_LEADER_REGEX = re.compile(r'\.{3,}|\u2026')

def extract_headings(doc: pymupdf.Document) -> tuple[list[dict], str]:
    num_pages = len(doc)
    
    # 1. Outline (Bookmarks)
    try:
        raw_toc = doc.get_toc() # list of [lvl, title, page]
        if raw_toc and len(raw_toc) >= 3:
            headings = []
            for item in raw_toc:
                lvl = max(1, min(4, int(item[0])))
                title = str(item[1]).strip()
                page = int(item[2])
                if 1 <= page <= num_pages and title:
                    headings.append({"title": title, "level": lvl, "page": page})
            
            deduped = dedupe_consecutive(headings)
            if len(deduped) >= 3:
                return deduped[:800], "outline"
    except Exception:
        pass

    # 2. Typographic Heuristics
    try:
        headings, count = extract_heuristic_headings(doc)
        if count >= 3:
            return headings[:800], "heuristic"
    except Exception:
        pass

    # 3. Synthetic Fallback (1 per page)
    synthetic = []
    for page_num in range(1, num_pages + 1):
        page = doc[page_num - 1]
        lines = [line.strip() for line in page.get_text("text").splitlines() if line.strip()]
        first_meaningful = f"Page {page_num}"
        for line in lines:
            # ignore bare numbers
            if line.isdigit() or len(line) < 3:
                continue
            first_meaningful = line[:80].strip()
            break
        synthetic.append({"title": first_meaningful, "level": 1, "page": page_num})

    return dedupe_consecutive(synthetic)[:800], "synthetic_first_line"


def extract_heuristic_headings(doc: pymupdf.Document) -> tuple[list[dict], int]:
    num_pages = len(doc)
    font_sizes = Counter()
    page_lines: list[list[dict]] = []
    line_page_presence = Counter()

    for p_idx in range(num_pages):
        page = doc[p_idx]
        p_num = p_idx + 1
        lines_on_page = []
        unique_texts_on_this_page = set()
        
        try:
            p_dict = page.get_text("dict")
        except Exception:
            p_dict = {}

        for block in p_dict.get("blocks", []):
            if block.get("type") == 0:  # text block
                for line in block.get("lines", []):
                    line_text = ""
                    max_size = 0.0
                    is_bold = False
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        line_text += text
                        sz = span.get("size", 10.0)
                        if sz > max_size:
                            max_size = sz
                        flags = span.get("flags", 0)
                        font_name = span.get("font", "").lower()
                        if (flags & 2 != 0) or ("bold" in font_name):
                            is_bold = True
                    
                    cleaned_line = line_text.strip()
                    if cleaned_line:
                        font_sizes[round(max_size, 1)] += len(cleaned_line)
                        lines_on_page.append({
                            "text": cleaned_line,
                            "size": max_size,
                            "bold": is_bold,
                            "page": p_num
                        })
                        unique_texts_on_this_page.add(cleaned_line.lower())

        for t in unique_texts_on_this_page:
            line_page_presence[t] += 1
            
        page_lines.append(lines_on_page)

    # Body font size = size mode weighted by character count
    body_size = 10.0
    if font_sizes:
        body_size = font_sizes.most_common(1)[0][0]

    header_threshold = max(2, int(num_pages * 0.30))

    candidate_headings = []
    for lines_on_page in page_lines:
        for item in lines_on_page:
            text = item["text"]
            size = item["size"]
            bold = item["bold"]
            page = item["page"]
            
            # Exclusions:
            # 1. >120 chars
            if len(text) > 120:
                continue
            # 2. Bare page numbers
            if text.isdigit():
                continue
            # 3. Repeated headers/footers (>30% of pages)
            if line_page_presence[text.lower()] > header_threshold:
                continue
            # 4. Dot leaders in TOC
            if DOT_LEADER_REGEX.search(text):
                continue

            # Candidate checks
            is_large = size >= (1.15 * body_size)
            is_bold_title = bold and len(text) <= 100 and not text.endswith(('.', ','))
            is_numbered = bool(NUMBERING_REGEX.match(text))
            is_keyword = bool(KEYWORDS_REGEX.match(text))
            words = text.split()
            is_all_caps = text.isupper() and 1 <= len(words) <= 8 and any(c.isalpha() for c in text)

            if is_large or is_bold_title or is_numbered or is_keyword or is_all_caps:
                # Level determination
                level = 1
                if size >= 1.5 * body_size:
                    level = 1
                elif size >= 1.25 * body_size:
                    level = 2
                elif is_numbered:
                    m = NUMBERING_REGEX.match(text)
                    if m:
                        num_part = m.group(1)
                        depth = len(num_part.split('.'))
                        level = min(4, depth)
                    else:
                        level = 2
                else:
                    level = 3

                candidate_headings.append({
                    "title": text,
                    "level": level,
                    "page": page
                })

    deduped = dedupe_consecutive(candidate_headings)
    return deduped, len(deduped)

def dedupe_consecutive(headings: list[dict]) -> list[dict]:
    res = []
    last_title = None
    for h in headings:
        title = h["title"].strip()
        if not title:
            continue
        if title != last_title:
            res.append(h)
            last_title = title
    return res
