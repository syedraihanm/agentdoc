import uuid
import asyncio
import time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from backend.app.storage.repo import Repo
from backend.app.api.deps import get_repo, get_llm_client
from backend.app.api.sse import broadcaster
from backend.app.tools.backend import ToolBackend
from backend.app.tools.gateway import ToolGateway, Budget
from backend.app.agent.controller import AgentController
from backend.app.agent.llm.base import LLMClient
from backend.app.config import settings

router = APIRouter(prefix="/sessions", tags=["chat"])

# In-memory tracking of active runs per session
active_sessions: dict[str, str] = {} # session_id -> run_id

class CreateSessionReq(BaseModel):
    doc_id: str | None = None
    doc_ids: list[str] | None = None

class AddDocumentReq(BaseModel):
    doc_id: str

class AskQuestionReq(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

@router.post("", status_code=201)
async def create_session(req: CreateSessionReq, repo: Repo = Depends(get_repo)):
    raw_ids = req.doc_ids or ([req.doc_id] if req.doc_id else [])
    if not raw_ids:
        raise HTTPException(status_code=400, detail={"code": "missing_doc_id", "message": "At least one doc_id is required."})
    
    # Validate documents exist
    validated_ids = []
    for did in raw_ids:
        d = repo.get_document(did)
        if not d:
            raise HTTPException(status_code=404, detail={"code": "doc_not_found", "message": f"Document '{did}' not found"})
        validated_ids.append(did)

    session_id = str(uuid.uuid4())[:8]
    created_at = datetime.now(timezone.utc).isoformat()
    repo.create_session(session_id, validated_ids, created_at)
    return {"session_id": session_id, "doc_id": validated_ids[0], "doc_ids": validated_ids}

@router.post("/{session_id}/documents", status_code=200)
async def add_document(session_id: str, req: AddDocumentReq, repo: Repo = Depends(get_repo)):
    sess = repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Session not found"})
    doc = repo.get_document(req.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "doc_not_found", "message": f"Document '{req.doc_id}' not found"})
    added_at = datetime.now(timezone.utc).isoformat()
    repo.add_document_to_session(session_id, req.doc_id, added_at)
    updated_sess = repo.get_session(session_id)
    return {"session_id": session_id, "doc_ids": updated_sess.get("doc_ids", [])}

@router.get("/{session_id}")
async def get_session(session_id: str, repo: Repo = Depends(get_repo)):
    sess = repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Session not found"})
    runs = repo.list_runs_for_session(session_id)
    doc = repo.get_document(sess["doc_id"])
    return {
        "session_id": session_id,
        "doc": doc,
        "documents": sess.get("documents", [doc] if doc else []),
        "doc_ids": sess.get("doc_ids", [sess["doc_id"]]),
        "runs": runs,
        "active_run_id": active_sessions.get(session_id)
    }

def run_agent_task(
    run_id: str,
    session_id: str,
    doc_ids: list[str],
    num_pages: int,
    question: str,
    history: list[dict],
    repo: Repo,
    llm: LLMClient,
    doc_catalogue: list[dict] | None = None
):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    seq_counter = 0

    def on_event(event_type: str, payload: dict):
        nonlocal seq_counter
        seq_counter += 1
        ts = datetime.now(timezone.utc).isoformat()
        repo.save_event(run_id, seq_counter, ts, event_type, payload)
        loop.run_until_complete(broadcaster.broadcast(run_id, event_type, payload))

    def on_tool_event(tool_event: dict):
        on_event("tool_call", tool_event)

    try:
        backend = ToolBackend(repo)
        budget = Budget(max_calls=settings.TOOL_BUDGET)
        gateway = ToolGateway(backend, doc_id=doc_ids, budget=budget, on_event=on_tool_event)
        
        primary_did = doc_ids[0] if doc_ids else ""
        controller = AgentController(
            gateway=gateway,
            llm=llm,
            session_id=session_id,
            doc_id=primary_did,
            num_pages=num_pages,
            conversation_history=history,
            on_event=on_event,
            doc_catalogue=doc_catalogue
        )

        verified_ans = controller.run(question)
        status_val = verified_ans.answer_obj.status
        answer_json_str = verified_ans.answer_obj.model_dump_json()

        finished_at = datetime.now(timezone.utc).isoformat()
        repo.update_run(
            run_id=run_id,
            status=status_val,
            answer_json=answer_json_str,
            tool_calls_used=budget.used,
            llm_calls=controller.llm_calls_count,
            finished_at=finished_at,
            latency_ms=0
        )
    except Exception as e:
        finished_at = datetime.now(timezone.utc).isoformat()
        err_payload = {"code": "run_failed", "message": str(e)}
        on_event("error", err_payload)
        repo.update_run(
            run_id=run_id,
            status="error",
            answer_json=None,
            tool_calls_used=0,
            llm_calls=0,
            finished_at=finished_at,
            latency_ms=0
        )
    finally:
        active_sessions.pop(session_id, None)
        loop.close()

@router.post("/{session_id}/ask", status_code=202)
async def ask_question(
    session_id: str,
    req: AskQuestionReq,
    background_tasks: BackgroundTasks,
    repo: Repo = Depends(get_repo),
    llm: LLMClient = Depends(get_llm_client)
):
    sess = repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Session not found"})
    
    if session_id in active_sessions:
        raise HTTPException(status_code=409, detail={"code": "run_active", "message": "A question is already being processed in this session."})

    doc_ids = sess.get("doc_ids") or [sess["doc_id"]]
    doc_catalogue = sess.get("documents", [])
    primary_doc = doc_catalogue[0] if doc_catalogue else repo.get_document(doc_ids[0])
    if not primary_doc and not doc_catalogue:
        raise HTTPException(status_code=404, detail={"code": "doc_not_found", "message": "Document not found"})
    num_pages = primary_doc.get("num_pages", 1) if primary_doc else 1

    run_id = str(uuid.uuid4())[:8]
    active_sessions[session_id] = run_id
    started_at = datetime.now(timezone.utc).isoformat()
    repo.create_run(run_id, session_id, req.question, "running", started_at)

    # Fetch prior history turns
    prior_runs = repo.list_runs_for_session(session_id)
    history = []
    for r in prior_runs:
        if r["run_id"] != run_id and r.get("answer"):
            history.append({
                "question": r["question"],
                "answer": r["answer"].get("answer", "")
            })

    background_tasks.add_task(
        run_agent_task,
        run_id=run_id,
        session_id=session_id,
        doc_ids=doc_ids,
        num_pages=num_pages,
        question=req.question,
        history=history,
        repo=repo,
        llm=llm,
        doc_catalogue=doc_catalogue
    )

    return {"run_id": run_id}