from pathlib import Path
import pymupdf
from backend.app.ingestion.headings import extract_headings

def test_headings_outline_and_heuristic():
    p_outline = Path("data/demo_helix_policy.pdf")
    p_no_outline = Path("data/demo_helix_policy_no_outline.pdf")
    
    assert p_outline.exists()
    assert p_no_outline.exists()

    # 1. Outline variant
    doc1 = pymupdf.open(str(p_outline))
    h1, src1 = extract_headings(doc1)
    assert src1 == "outline"
    assert len(h1) >= 8
    titles1 = [h["title"] for h in h1]
    assert any("Remote Work" in t for t in titles1)
    assert any("Amendment 1" in t for t in titles1)
    assert any("Errata" in t for t in titles1)
    doc1.close()

    # 2. Heuristic variant
    doc2 = pymupdf.open(str(p_no_outline))
    h2, src2 = extract_headings(doc2)
    assert src2 == "heuristic"
    assert len(h2) >= 6
    titles2 = [h["title"] for h in h2]
    assert any("Remote Work" in t for t in titles2)
    doc2.close()