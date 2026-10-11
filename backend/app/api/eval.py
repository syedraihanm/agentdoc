from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from backend.app.storage.repo import Repo
from backend.app.api.deps import get_repo, get_llm_client
from backend.app.eval.runner import run_evaluation
from backend.app.agent.llm.base import LLMClient
from scripts.make_demo_pdf import create_demo_pdf
from backend.app.ingestion.pdf_loader import ingest_pdf
from backend.app.config import settings

router = APIRouter(prefix="/eval", tags=["eval"])

class RunEvalReq(BaseModel):
    doc_id: str | None = None
    case_ids: list[str] | None = None

@router.post("/run")
async def trigger_eval(
    req: RunEvalReq,
    repo: Repo = Depends(get_repo),
    llm: LLMClient = Depends(get_llm_client)
):
    target_doc_id = req.doc_id
    if not target_doc_id:
        demo_pdf = settings.BASE_DIR / "data" / "demo_helix_policy.pdf"
        if not demo_pdf.exists():
            create_demo_pdf(demo_pdf, include_outline=True)
        doc = ingest_pdf(demo_pdf, "demo_helix_policy.pdf", repo)
        target_doc_id = doc["doc_id"]

    summary = run_evaluation(target_doc_id, repo, llm, req.case_ids)
    return summary

@router.get("/{eval_id}")
async def get_eval(eval_id: str, repo: Repo = Depends(get_repo)):
    results = repo.get_eval_results(eval_id)
    if not results:
        raise HTTPException(status_code=404, detail={"code": "eval_not_found", "message": "Evaluation run not found"})
    passed = sum(1 for r in results if r["passed"])
    return {
        "eval_id": eval_id,
        "total": len(results),
        "passed": passed,
        "pass_rate": round(passed / len(results) * 100, 1),
        "cases": results
    }