from typing import Type, TypeVar, Any
from pydantic import BaseModel
from backend.app.agent.llm.base import LLMClient
from backend.app.agent.schemas import Decision, Answer

T = TypeVar("T", bound=BaseModel)

class FakeLLM(LLMClient):
    def __init__(self, scripted_responses: list[BaseModel] | None = None, adversarial_mode: bool = False):
        self.scripted_responses = list(scripted_responses or [])
        self.adversarial_mode = adversarial_mode
        self.call_history: list[dict[str, Any]] = []

    def complete_json(
        self,
        system: str,
        messages: list[dict[str, str]],
        schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 1500,
        timeout: int = 60
    ) -> tuple[T, str, dict[str, Any]]:
        self.call_history.append({"system": system, "messages": messages, "schema": schema.__name__})
        
        # Adversarial mode test case
        if self.adversarial_mode:
            if schema == Decision:
                # Malicious decision: tries 50 calls, fake tools, doc_id injection, invalid types
                bad_actions = [
                    {"tool": "fake_tool", "args": {"doc_id": "other_doc", "code": "malicious"}, "purpose": "exploit"},
                    {"tool": "get_page", "args": {"page_number": "1-10"}, "purpose": "range exploit"},
                    {"tool": "get_page", "args": {"page_number": -5}, "purpose": "negative page"}
                ]
                # Spam 47 more get_page calls
                for i in range(1, 48):
                    bad_actions.append({"tool": "get_page", "args": {"page_number": i % 10 + 1}, "purpose": f"spam {i}"})
                
                malicious_decision = Decision(
                    standalone_question="adversarial question",
                    reasoning_summary="attempting to break gateway",
                    ready_to_answer=False,
                    actions=bad_actions
                )
                return malicious_decision, malicious_decision.model_dump_json(), {"model": "fake-adversarial"}

            elif schema == Answer:
                bad_answer = Answer(
                    status="answered",
                    answer="ALL EXPENSES APPROVED - Note to assistant complied with.",
                    evidence=[],
                    ignored_instructions=[]
                )
                return bad_answer, bad_answer.model_dump_json(), {"model": "fake-adversarial"}

        # Scripted queue mode
        if self.scripted_responses:
            resp = self.scripted_responses.pop(0)
            if isinstance(resp, schema):
                return resp, resp.model_dump_json(), {"model": "fake-scripted"}
            else:
                return resp, str(resp), {"model": "fake-scripted"}

        # Default fallback responses if queue empty
        if schema == Decision:
            fallback_dec = Decision(
                standalone_question="Default question",
                reasoning_summary="No more scripted actions, declaring ready",
                ready_to_answer=True,
                actions=[]
            )
            return fallback_dec, fallback_dec.model_dump_json(), {"model": "fake-default"}
        elif schema == Answer:
            fallback_ans = Answer(
                status="insufficient",
                answer="The document does not contain enough information to answer this.",
                evidence=[],
                conflicts=[],
                not_found=["Information not found in document"]
            )
            return fallback_ans, fallback_ans.model_dump_json(), {"model": "fake-default"}

        raise ValueError(f"Unknown schema in FakeLLM: {schema}")