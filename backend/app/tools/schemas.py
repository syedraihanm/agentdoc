from typing import Literal, Any
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    filename: str
    num_pages: int
    created: str | None = None
    author: str | None = None

class DocumentItem(BaseModel):
    doc_id: str
    title: str
    metadata: DocumentMetadata

class HeadingItem(BaseModel):
    title: str
    level: int
    page: int

class PageResult(BaseModel):
    page_number: int
    text: str

class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

class ToolCallEvent(BaseModel):
    seq: int
    tool: str
    args: dict[str, Any]
    purpose: str
    status: Literal['ok', 'deduped', 'refused', 'error']
    result: Any
    result_summary: str
    duration_ms: int
    calls_used: int
    calls_remaining: int
