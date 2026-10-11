import re
import unicodedata

# Mapping for curly quotes and typographic dashes
CHAR_MAP = {
    '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",
    '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
    '\u2013': '-', '\u2014': '-', '\u2015': '-', '\u2212': '-',
    '\u00ad': '',  # soft hyphen
}

def remove_diacritics(text: str) -> str:
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

def normalize_text(text: str) -> str:
    """Standard search normalization: NFKC, ascii quotes/dashes, de-hyphenation, lowercase, single-spaced."""
    if not text:
        return ""
    # 1. NFKC normalization
    s = unicodedata.normalize('NFKC', text)
    
    # 2. Map typographic characters
    for k, v in CHAR_MAP.items():
        s = s.replace(k, v)
        
    # 3. Strip diacritics and lowercase
    s = remove_diacritics(s).lower()
    
    # 4. Re-join line-break hyphenation: e.g. "inter-\n national" -> "international"
    s = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', s)
    
    # 5. Collapse all whitespace to a single space
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def normalize_numeric_variant(norm_text: str) -> str:
    """Strips currency symbols and thousand separator commas/dots between digits: ,500 -> 1500."""
    if not norm_text:
        return ""
    s = norm_text
    # Remove currency symbols ($ € £ ¥ ₹)
    s = re.sub(r'[$€£¥₹]', '', s)
    # Remove commas between digits: 1,500 -> 1500
    s = re.sub(r'(?<=\d),(?=\d)', '', s)
    # Collapse any resulting double spaces
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def validate_keyword(keyword: str) -> tuple[bool, str]:
    """Validates keyword constraints: 2-80 chars after trimming; at least 1 alphanumeric char."""
    k = keyword.strip()
    if len(k) < 2:
        return False, "Keyword too short (minimum 2 characters)"
    if len(k) > 80:
        return False, "Keyword too long (maximum 80 characters)"
    if not any(c.isalnum() for c in k):
        return False, "Keyword must contain at least one alphanumeric character"
    return True, ""
