from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator

class DecisionAction(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_action(cls, data: Any) -> Any:
        if isinstance(data, dict):
            t = data.get("tool") or data.get("name") or data.get("action") or ""
            data["tool"] = str(t)
            if "args" not in data or not isinstance(data.get("args"), dict):
                args = {}
                for k in ["keyword", "page_number", "page", "doc_id", "doc"]:
                    if k in data:
                        args["page_number" if k == "page" else ("doc_id" if k == "doc" else k)] = data[k]
                data["args"] = args
            elif isinstance(data.get("args"), dict) and "doc" in data["args"] and "doc_id" not in data["args"]:
                data["args"]["doc_id"] = data["args"]["doc"]
        return data

class Decision(BaseModel):
    standalone_question: str = Field(default="", description="Rewrite of question resolving pronouns/ellipsis from history")
    question_type: Literal[
        "lookup", "multi_page", "comparison", "numeric",
        "rule_with_exceptions", "list_all", "unanswerable_suspected"
    ] = "lookup"
    reasoning_summary: str = Field(default="", description="<= 60 words for the user trace explaining why these actions")
    ready_to_answer: bool = False
    actions: list[DecisionAction] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_decision(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("reasoning_summary"):
                data["reasoning_summary"] = data.get("thought") or data.get("reasoning") or data.get("summary") or "Planning next document tool calls"
            if not data.get("standalone_question"):
                data["standalone_question"] = data.get("question") or ""
            if "question_type" not in data or data["question_type"] not in (
                "lookup", "multi_page", "comparison", "numeric",
                "rule_with_exceptions", "list_all", "unanswerable_suspected"
            ):
                data["question_type"] = "lookup"
        return data

class EvidenceItem(BaseModel):
    page: int
    quote: str
    supports: str
    doc_id: str | None = None

class ConflictChosen(BaseModel):
    page: int
    quote: str
    doc_id: str | None = None

class ConflictItem(BaseModel):
    topic: str
    chosen: ConflictChosen
    superseded: list[ConflictChosen]
    resolution_rule: Literal[
        "explicit_supersession", "later_effective_date",
        "amendment_or_errata", "specific_over_general", "unresolved"
    ]

class CalculationOperand(BaseModel):
    value: float | int
    page: int
    doc_id: str | None = None

class CalculationItem(BaseModel):
    expression: str
    result: float | int
    operands: list[CalculationOperand] = Field(default_factory=list)

class IgnoredInstructionItem(BaseModel):
    page: int
    excerpt: str
    doc_id: str | None = None

class Answer(BaseModel):
    status: Literal["answered", "partial", "insufficient"]
    answer: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    calculation: CalculationItem | None = None
    not_found: list[str] = Field(default_factory=list)
    searched_summary: str | None = None
    closest_related: str | None = None
    confidence: Literal["high", "medium", "low"] = "high"
    ignored_instructions: list[IgnoredInstructionItem] = Field(default_factory=list)

class VerifiedAnswer(BaseModel):
    answer_obj: Answer
    verification: dict[str, Any] = Field(default_factory=dict)