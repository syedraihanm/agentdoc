import pytest
from backend.app.storage.repo import Repo
from backend.app.storage.db import init_db
from backend.app.tools.backend import ToolBackend
from backend.app.tools.gateway import ToolGateway, Budget
from backend.app.agent.verifier import verify_answer
from backend.app.agent.schemas import Answer, EvidenceItem

@pytest.fixture
def multi_doc_repo(tmp_path):
    db_path = tmp_path / "multi_doc.db"
    init_db(db_path)
    repo = Repo(db_path)
    
    # Save Doc A
    repo.save_document("doc_a", "Travel Policy", "travel.pdf", "hash_a", 5, "outline", 3, None, None, [], "2026-01-01")
    repo.save_pages("doc_a", [
        {"page_number": 1, "text": "Travel rules: Per diem is $75.", "norm": "travel rules: per diem is $75.", "norm_numeric": "travel rules: per diem is 75."},
        {"page_number": 2, "text": "Flights must be economy class.", "norm": "flights must be economy class.", "norm_numeric": "flights must be economy class."}
    ])
    repo.save_headings("doc_a", [
        {"title": "Per Diem", "level": 1, "page": 1},
        {"title": "Flight Booking", "level": 1, "page": 2}
    ])
    
    # Save Doc B
    repo.save_document("doc_b", "Remote Work Policy", "remote.pdf", "hash_b", 10, "outline", 2, None, None, [], "2026-01-02")
    repo.save_pages("doc_b", [
        {"page_number": 1, "text": "Remote stipend is $500 per year.", "norm": "remote stipend is $500 per year.", "norm_numeric": "remote stipend is 500 per year."}
    ])
    repo.save_headings("doc_b", [
        {"title": "Equipment Stipend", "level": 1, "page": 1}
    ])
    
    # Save an Unrelated Doc C (uploaded in past)
    repo.save_document("doc_c", "Secret Roadmap", "secret.pdf", "hash_c", 2, "synthetic", 1, None, None, [], "2025-12-01")
    
    return repo

def test_gateway_multi_doc_isolation_and_scoping(multi_doc_repo):
    backend = ToolBackend(multi_doc_repo)
    budget = Budget(max_calls=6)
    
    # Session with doc_a and doc_b (doc_c is excluded)
    gw = ToolGateway(backend, doc_id=["doc_a", "doc_b"], budget=budget)
    
    # 1. list_documents only returns doc_a and doc_b, NOT doc_c
    ok, res, st = gw.execute("list_documents")
    assert ok is True
    assert budget.used == 1
    returned_ids = {d["doc_id"] for d in res}
    assert returned_ids == {"doc_a", "doc_b"}
    assert "doc_c" not in returned_ids
    
    # 2. Omitting doc_id in multi-doc session is refused without burning budget
    ok, res, st = gw.execute("get_page", {"page_number": 1})
    assert ok is False
    assert st == "refused"
    assert "Multi-document session requires 'doc_id'" in res
    assert budget.used == 1  # did not spend budget
    
    # 3. Specifying doc_c (outside session) is refused without burning budget
    ok, res, st = gw.execute("get_page", {"doc_id": "doc_c", "page_number": 1})
    assert ok is False
    assert st == "refused"
    assert "Forbidden doc_id 'doc_c'" in res
    assert budget.used == 1  # did not spend budget
    
    # 4. Valid doc_id succeeds and spends 1 budget
    ok, res, st = gw.execute("get_page", {"doc_id": "doc_a", "page_number": 1})
    assert ok is True
    assert st == "ok"
    assert res["page_number"] == 1
    assert "Per diem is $75" in res["text"]
    assert budget.used == 2
    
    # 5. Search in doc_b
    ok, res, st = gw.execute("search_keyword", {"doc_id": "doc_b", "keyword": "stipend"})
    assert ok is True
    assert res == [1]
    assert budget.used == 3

def test_verifier_multi_doc_attribution():
    pages = {
        ("doc_a", 1): "Per diem allowance is $75 for meals.",
        ("doc_b", 1): "Remote work stipend is $500 annually."
    }
    
    # Case 1: Correctly attributed quotes
    ans = Answer(
        status="answered",
        answer="The travel meal per diem is $75 (p. 1) and remote stipend is $500 (p. 1).",
        evidence=[
            EvidenceItem(doc_id="doc_a", page=1, quote="Per diem allowance is $75 for meals", supports="meal per diem"),
            EvidenceItem(doc_id="doc_b", page=1, quote="Remote work stipend is $500 annually", supports="remote stipend")
        ]
    )
    v = verify_answer(ans, pages, "What are the allowances?")
    assert v.answer_obj.status == "answered"
    assert len(v.answer_obj.evidence) == 2
    
    # Case 2: Wrong doc attribution drops quote
    ans_mismatched = Answer(
        status="answered",
        answer="Per diem is $75.",
        evidence=[
            # Quote exists in doc_a, but falsely attributed to doc_b
            EvidenceItem(doc_id="doc_b", page=1, quote="Per diem allowance is $75 for meals", supports="meal per diem")
        ]
    )
    v2 = verify_answer(ans_mismatched, pages, "What is the per diem?")
    assert v2.answer_obj.status == "insufficient"
    assert len(v2.answer_obj.evidence) == 0
    assert any(d["reason"] == "quote_not_found_on_page" for d in v2.verification["dropped_quotes"])
