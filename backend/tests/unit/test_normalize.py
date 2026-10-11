import pytest
from backend.app.ingestion.normalize import normalize_text, normalize_numeric_variant, validate_keyword

def test_normalize_quotes_dashes():
    raw = '“Hello”—‘World’ – test−minus'
    norm = normalize_text(raw)
    assert '"hello"-\'world\' - test-minus' == norm

def test_normalize_ligatures_nfkc():
    raw = 'ﬁrst ﬂight'
    norm = normalize_text(raw)
    assert norm == 'first flight'

def test_normalize_hyphenation():
    raw = 'inter-\n national cooperation'
    norm = normalize_text(raw)
    assert norm == 'international cooperation'

def test_normalize_diacritics():
    raw = 'Café résumé'
    norm = normalize_text(raw)
    assert norm == 'cafe resume'

def test_normalize_numeric_variant():
    raw = '$1,500 per month or €2,000'
    norm = normalize_text(raw)
    assert norm == '$1,500 per month or €2,000'
    num_norm = normalize_numeric_variant(norm)
    assert num_norm == '1500 per month or 2000'

def test_validate_keyword():
    assert validate_keyword('remote')[0] is True
    assert validate_keyword('a')[0] is False  # too short
    assert validate_keyword('   ')[0] is False
    assert validate_keyword('!@#$%')[0] is False  # no alphanumeric
    assert validate_keyword('a' * 81)[0] is False  # too long