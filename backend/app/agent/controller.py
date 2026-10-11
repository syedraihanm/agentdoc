import time
from datetime import datetime, timezone
from typing import Callable, Any
from backend.app.config import settings
from backend.app.tools.gateway import ToolGateway
from backend.app.agent.schemas import Decision, Answer, VerifiedAnswer
from backend.app.agent.llm.base import LLMClient
from backend.app.agent.smalltalk import check_smalltalk
from backend.app.agent.ledger import EvidenceLedger
from backend.app.agent.prompts import (
    DECIDE_SYSTEM_PROMPT, ANSWER_SYSTEM_PROMPT,
    render_decide_input, render_answer_input
)
from backend.app.agent.verifier import verify_answer

class AgentController:
    def __init__(
        self,
        gateway: ToolGateway,
        llm: LLMClient,
        session_id: str,
        doc_id: str,
        num_pages: int,
        conversation_history: list[dict] | None = None,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
        doc_catalogue: list[dict[str, Any]] | None = None
    ):
        self.gateway = gateway
        self.llm = llm
        self.session_id = session_id
        self.doc_id = doc_id
        self.num_pages = num_pages
        self.conversation_history = conversation_history or []
        self.on_event = on_event
        self.doc_catalogue = doc_catalogue or []
        self.llm_calls_count = 0

    def _emit(self, event_type: str, payload: dict[str, Any]):
        if self.on_event:
            self.on_event(event_type, payload)

    def run(self, user_question: str) -> VerifiedAnswer:
        start_time = time.perf_counter()
        self._emit("run_started", {
            "question": user_question,
            "session_id": self.session_id,
            "doc_id": self.doc_id,
            "config": {
                "budget": self.gateway.budget.max_calls,
                "max_decide_rounds": settings.MAX_DECIDE_ROUNDS,
                "reserve_calls": settings.RESERVE_CALLS
            }
        })

        # 1. SMALLTALK CHECK
        canned_reply = check_smalltalk(user_question)
        if canned_reply:
            answer = Answer(
                status="answered",
                answer=canned_reply,
                evidence=[],
                conflicts=[],
                not_found=[],
                confidence="high"
            )
            v_ans = VerifiedAnswer(answer_obj=answer, verification={"smalltalk": True})
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            self._emit("final", {
                "answer": v_ans.model_dump(),
                "tool_calls_used": 0,
                "llm_calls_count": 0,
                "total_latency_ms": latency_ms
            })
            return v_ans

        # 2. STRUCTURAL ORIENTATION
        # If single-doc: Execute list_headings as Call #1 automatically
        # If multi-doc: Do not burn Call #1 blindly; provide doc catalogue in ledger and let LLM route
        is_multi_doc = len(self.doc_catalogue) > 1
        if not is_multi_doc:
            ok, headings_res, status = self.gateway.execute("list_headings", purpose="Map document structure and outline")
            headings = headings_res if ok and isinstance(headings_res, list) else []
            ledger = EvidenceLedger(
                headings=headings,
                num_pages=self.num_pages,
                doc_catalogue=self.doc_catalogue,
                primary_doc_id=self.doc_id
            )
            ledger.record_call("list_headings", {"doc_id": self.doc_id}, "Map document structure", headings, status)
        else:
            headings_by_doc = {}
            for d in self.doc_catalogue:
                did = d.get("doc_id")
                if did:
                    try:
                        h_list = self.gateway.backend.list_headings(did)
                        if h_list:
                            headings_by_doc[did] = h_list
                    except Exception:
                        pass

            primary_headings = headings_by_doc.get(self.doc_id, [])
            ledger = EvidenceLedger(
                headings=primary_headings,
                num_pages=self.num_pages,
                doc_catalogue=self.doc_catalogue,
                primary_doc_id=self.doc_id
            )
            ledger.headings_by_doc = headings_by_doc

        standalone_question = user_question
        ready_to_answer = False

        # 3. DECIDE & ACT LOOPS (Rounds 1 to MAX_DECIDE_ROUNDS)
        for round_num in range(1, settings.MAX_DECIDE_ROUNDS + 1):
            if not self.gateway.budget.can_spend() or ready_to_answer:
                break

            ledger_text = ledger.render_ledger(self.gateway.budget.used, self.gateway.budget.remaining)
            decide_input = render_decide_input(
                conversation_history=self.conversation_history[-settings.HISTORY_TURNS:],
                user_question=user_question,
                round_num=round_num,
                max_rounds=settings.MAX_DECIDE_ROUNDS,
                budget_used=self.gateway.budget.used,
                budget_remaining=self.gateway.budget.remaining,
                ledger_text=ledger_text
            )

            # LLM Decide Call
            self.llm_calls_count += 1
            try:
                decide_obj, raw_text, usage = self.llm.complete_json(
                    system=DECIDE_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": decide_input}],
                    schema=Decision,
                    temperature=settings.LLM_TEMPERATURE
                )
                self._emit("llm_call", {
                    "purpose": f"decide_{round_num}",
                    "usage": usage,
                    "raw_output": raw_text[:200]
                })
            except Exception as e:
                self._emit("error", {"code": "llm_decide_error", "message": str(e), "recoverable": True})
                break

            standalone_question = decide_obj.standalone_question or standalone_question
            ready_to_answer = decide_obj.ready_to_answer

            self._emit("decision", {
                "round": round_num,
                "reasoning": decide_obj.reasoning_summary,
                "ready_to_answer": ready_to_answer,
                "proposed_actions": [a.model_dump() for a in decide_obj.actions]
            })

            if ready_to_answer:
                break

            # Controller Rules for Actions:
            proposed = decide_obj.actions
            if not proposed:
                # C4: No progress rule
                break

            # C1 & C2: Reserve & Budget Trimming
            remaining = self.gateway.budget.remaining
            max_can_execute = remaining
            if round_num <= 2:
                max_can_execute = max(0, remaining - settings.RESERVE_CALLS)
            
            # Trim from end if exceeds allowable
            executable_actions = proposed[:max_can_execute]
            if not executable_actions:
                # If cannot execute more under reserve, spend reserve in next round or answer
                if round_num >= 2:
                    executable_actions = proposed[:remaining]

            if not executable_actions:
                break

            # ACT: Execute actions sequentially
            for act in executable_actions:
                if not self.gateway.budget.can_spend():
                    break
                ok_act, res_act, st_act = self.gateway.execute(
                    act.tool,
                    act.args,
                    purpose=act.purpose
                )
                ledger.record_call(act.tool, act.args, act.purpose, res_act, st_act)

        # 4. FINAL ANSWER LLM CALL (Exactly 1 call, no tools)
        self.llm_calls_count += 1
        final_ledger_text = ledger.render_ledger(self.gateway.budget.used, self.gateway.budget.remaining)
        answer_input = render_answer_input(
            user_question=user_question,
            standalone_question=standalone_question,
            conversation_history=self.conversation_history[-settings.HISTORY_TURNS:],
            ledger_text=final_ledger_text,
            tool_calls_count=self.gateway.budget.used
        )

        try:
            answer_obj, raw_ans, usage_ans = self.llm.complete_json(
                system=ANSWER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": answer_input}],
                schema=Answer,
                temperature=settings.LLM_TEMPERATURE
            )
            self._emit("llm_call", {
                "purpose": "final_answer",
                "usage": usage_ans,
                "raw_output": raw_ans[:200]
            })
        except Exception as e:
            self._emit("error", {"code": "llm_answer_error", "message": str(e), "recoverable": False})
            answer_obj = Answer(
                status="insufficient",
                answer="The document does not contain enough information to answer this.",
                evidence=[],
                not_found=["LLM could not produce structured answer"]
            )

        # 5. DETERMINISTIC VERIFICATION LAYER
        verified = verify_answer(
            answer=answer_obj,
            fetched_pages=ledger.pages_read,
            user_question=user_question,
            ledger_signals={"headings": ledger.headings, "injection_flags": ledger.injection_flags}
        )
        self._emit("verification", verified.verification)

        # 6. FINAL WRAPUP
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        self._emit("final", {
            "answer": verified.model_dump(),
            "tool_calls_used": self.gateway.budget.used,
            "llm_calls_count": self.llm_calls_count,
            "total_latency_ms": latency_ms
        })

        return verified