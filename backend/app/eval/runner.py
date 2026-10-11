import json
import uuid
from pathlib import Path
from typing import Any
from backend.app.config import settings
from backend.app.storage.repo import Repo
from backend.app.tools.backend import ToolBackend
from backend.app.tools.gateway import ToolGateway, Budget
from backend.app.agent.controller import AgentController
from backend.app.agent.llm.base import LLMClient

def run_evaluation(
    doc_id: str,
    repo: Repo,
    llm: LLMClient,
    case_ids: list[str] | None = None
) -> dict[str, Any]:
    cases_file = Path(__file__).parent / "cases.json"
    with open(cases_file, "r", encoding="utf-8") as f:
        cases: list[dict] = json.load(f)

    if case_ids:
        cases = [c for c in cases if c["id"] in case_ids]

    doc = repo.get_document(doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found.")

    eval_id = str(uuid.uuid4())[:8]
    results = []
    passed_count = 0
    budget_compliant_count = 0

    conversation_history = []

    for c in cases:
        cid = c["id"]
        question = c["question"]
        expected_status = c["expected_status"]
        must_contain = c.get("must_contain", [])
        must_not_contain = c.get("must_not_contain", [])

        backend = ToolBackend(repo)
        budget = Budget(max_calls=settings.TOOL_BUDGET)
        gateway = ToolGateway(backend, doc_id=doc_id, budget=budget)
        
        ctrl = AgentController(
            gateway=gateway,
            llm=llm,
            session_id=f"eval_{eval_id}",
            doc_id=doc_id,
            num_pages=doc["num_pages"],
            conversation_history=conversation_history
        )

        try:
            verified_ans = ctrl.run(question)
            ans_obj = verified_ans.answer_obj
            answer_text = ans_obj.answer

            # Checks
            status_ok = (ans_obj.status == expected_status)
            budget_ok = (budget.used <= settings.TOOL_BUDGET)
            if budget_ok:
                budget_compliant_count += 1

            contain_ok = True
            if must_contain:
                contain_ok = any(mc.lower() in answer_text.lower() for mc in must_contain)

            not_contain_ok = True
            for mnc in must_not_contain:
                if mnc.lower() in answer_text.lower():
                    not_contain_ok = False
                    break

            case_passed = status_ok and budget_ok and contain_ok and not_contain_ok
            if case_passed:
                passed_count += 1

            details = {
                "question": question,
                "expected_status": expected_status,
                "actual_status": ans_obj.status,
                "tool_calls_used": budget.used,
                "answer": answer_text,
                "contain_ok": contain_ok,
                "not_contain_ok": not_contain_ok,
                "evidence_quotes": [e.quote for e in ans_obj.evidence],
                "passed": case_passed
            }

            repo.save_eval_result(eval_id, cid, case_passed, details)
            results.append({"case_id": cid, "passed": case_passed, "details": details})

            # Append to history for follow-ups (e.g. Q13)
            conversation_history.append({"question": question, "answer": answer_text})

        except Exception as e:
            details = {
                "question": question,
                "error": str(e),
                "passed": False
            }
            repo.save_eval_result(eval_id, cid, False, details)
            results.append({"case_id": cid, "passed": False, "details": details})

    total = len(cases)
    pass_rate = (passed_count / total * 100) if total > 0 else 0
    budget_rate = (budget_compliant_count / total * 100) if total > 0 else 0

    return {
        "eval_id": eval_id,
        "doc_id": doc_id,
        "total": total,
        "passed": passed_count,
        "pass_rate": round(pass_rate, 1),
        "budget_compliance_rate": round(budget_rate, 1),
        "cases": results
    }