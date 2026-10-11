from backend.app.agent.verifier import verify_answer, normalize_for_quote_match, safe_eval_expression
from backend.app.agent.schemas import Answer, EvidenceItem, CalculationItem, CalculationOperand

def test_safe_eval_expression():
    assert safe_eval_expression("1500 - 1000") == 500
    assert safe_eval_expression("(20 + 30) * 2") == 100
    assert safe_eval_expression("__import__('os')") is None

def test_quote_match_tolerance():
    page_text = "Remote work is permitted up to 3 days per week."
    fetched = {4: page_text}

    # Exact match
    ans1 = Answer(
        status="answered",
        answer="Employees get 3 days per week.",
        evidence=[EvidenceItem(page=4, quote="Remote work is permitted up to 3 days per week.", supports="allowance")]
    )
    v1 = verify_answer(ans1, fetched, "How many days?")
    assert v1.answer_obj.status == "answered"
    assert v1.verification["v1_quotes_valid"] == 1

    # Fabricated quote dropped -> downgraded to insufficient
    ans2 = Answer(
        status="answered",
        answer="Employees get 10 days per week.",
        evidence=[EvidenceItem(page=4, quote="Remote work is permitted up to 10 days per week.", supports="fake")]
    )
    v2 = verify_answer(ans2, fetched, "How many days?")
    assert v2.answer_obj.status == "insufficient"
    assert v2.verification["v1_quotes_valid"] == 0
    assert len(v2.verification["dropped_quotes"]) == 1