import re
from typing import NamedTuple

class InjectionDetection(NamedTuple):
    pattern_index: int
    matched_text: str
    excerpt: str

INJECTION_PATTERNS = [
    re.compile(r'\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|all|any|the)\b.{0,40}\b(instruction|prompt|rule|question|system)s?', re.IGNORECASE),
    re.compile(r'\b(note|message|instruction|attention|important)s?\s*(to|for)\s*(the\s+)?(ai|assistant|llm|model|agent|chatbot|language model)\b', re.IGNORECASE),
    re.compile(r'\b(you are now|act as|pretend to be|new instructions?|system prompt|developer message)\b', re.IGNORECASE),
    re.compile(r'\b(reply|respond|answer|output|say|print|write)\b\s+(only\s+)?(with|that|exactly)\b', re.IGNORECASE),
    re.compile(r'\b(do not|don\'t|never)\s+(answer|use|call|search|mention|tell|reveal)\b', re.IGNORECASE),
    re.compile(r'\b(call|invoke|use|run|execute)\s+(the\s+)?(get_page|search_keyword|list_headings|list_documents|tool)\b', re.IGNORECASE),
    re.compile(r'</?\s*(system|assistant|user|developer|document_data|instructions?)\b', re.IGNORECASE),
]

def scan_text_for_injection(text: str) -> list[InjectionDetection]:
    detections = []
    for idx, pat in enumerate(INJECTION_PATTERNS):
        for match in pat.finditer(text):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 40)
            excerpt = text[start:end].replace('\n', ' ').strip()
            detections.append(InjectionDetection(idx, match.group(0), excerpt))
    return detections

def sanitize_document_text(text: str, boundary_token: str = "") -> str:
    """Escapes XML-like angle brackets and neutralizes boundary tokens."""
    if not text:
        return ""
    # Map < and > to full-width or harmless equivalents
    s = text.replace("<", "＜").replace(">", "＞")
    if boundary_token:
        s = s.replace(boundary_token, "[FILTERED_BOUNDARY]")
    return s