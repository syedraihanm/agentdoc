from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from backend.app.storage.repo import Repo
from backend.app.api.deps import get_repo
from backend.app.api.sse import event_generator

router = APIRouter(tags=["runs"])

@router.get("/runs/{run_id}")
async def get_run(run_id: str, repo: Repo = Depends(get_repo)):
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": "Run not found"})
    events = repo.get_events(run_id)
    run["events"] = events
    return run

@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str):
    return StreamingResponse(
        event_generator(run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.get("/runs/{run_id}/trace.json")
async def export_run_trace_json(run_id: str, repo: Repo = Depends(get_repo)):
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": "Run not found"})
    events = repo.get_events(run_id)
    return JSONResponse(content={"run": run, "events": events})

@router.get("/runs/{run_id}/trace.md")
async def export_run_trace_md(run_id: str, repo: Repo = Depends(get_repo)):
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"code": "run_not_found", "message": "Run not found"})
    events = repo.get_events(run_id)
    md = generate_markdown_trace(run, events)
    return PlainTextResponse(content=md, media_type="text/markdown")

@router.get("/sessions/{session_id}/trace.md")
async def export_session_trace_md(session_id: str, repo: Repo = Depends(get_repo)):
    sess = repo.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail={"code": "session_not_found", "message": "Session not found"})
    runs = repo.list_runs_for_session(session_id)
    doc = repo.get_document(sess["doc_id"])
    
    parts = [f"# Session Trace: {session_id}\n\nDocument: **{doc['title'] if doc else 'Unknown'}** ({doc['filename'] if doc else ''})\n\n---\n"]
    for r in runs:
        events = repo.get_events(r["run_id"])
        parts.append(generate_markdown_trace(r, events))
        parts.append("\n\n---\n")
    return PlainTextResponse(content="\n".join(parts), media_type="text/markdown")

def generate_markdown_trace(run: dict, events: list[dict]) -> str:
    lines = []
    lines.append(f"## Question: {run['question']}")
    lines.append(f"**Run ID:** `{run['run_id']}` | **Status:** `{run['status']}` | **Tool Calls:** {run.get('tool_calls_used', 0)}/6\n")

    # Table of Tool Calls
    lines.append("### Tool Calls Trace")
    lines.append("| # | Tool | Args | Result | Purpose | Used/6 |")
    lines.append("|---|------|------|--------|---------|--------|")
    
    tool_idx = 0
    for e in events:
        if e["type"] == "tool_call":
            p = e["payload"]
            tool_idx += 1
            args_str = ", ".join(f"{k}={v}" for k, v in p.get("args", {}).items() if k != "doc_id")
            lines.append(f"| {tool_idx} | `{p.get('tool')}` | `{args_str}` | {p.get('result_summary')} | {p.get('purpose')} | {p.get('calls_used')}/6 |")

    if tool_idx == 0:
        lines.append("| - | *No tool calls executed* | - | - | - | 0/6 |")

    # Final Answer
    lines.append("\n### Final Answer")
    ans = run.get("answer")
    if ans:
        lines.append(f"**Status:** `{ans.get('status')}` | **Confidence:** `{ans.get('confidence')}`\n")
        lines.append(f"> {ans.get('answer')}\n")
        if ans.get("evidence"):
            lines.append("**Evidence Quotes:**")
            for ev in ans["evidence"]:
                lines.append(f"- (p. {ev['page']}): *\"{ev['quote']}\"* — {ev.get('supports')}")
        if ans.get("conflicts"):
            lines.append("\n**Conflicts Resolved:**")
            for c in ans["conflicts"]:
                lines.append(f"- Topic: **{c['topic']}** (Rule: `{c['resolution_rule']}`)")
                lines.append(f"  - Chosen: (p. {c['chosen']['page']}) *\"{c['chosen']['quote']}\"*")
                for s in c.get("superseded", []):
                    lines.append(f"  - Superseded: (p. {s['page']}) ~~*\"{s['quote']}\"*~~")
        if ans.get("ignored_instructions"):
            lines.append("\n**Ignored Document Instructions:**")
            for ign in ans["ignored_instructions"]:
                lines.append(f"- (p. {ign['page']}): `{ign['excerpt']}`")
    else:
        lines.append("*No final answer recorded.*")

    return "\n".join(lines)