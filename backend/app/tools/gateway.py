import time
import re
import threading
from typing import Any, Callable
from backend.app.config import settings
from backend.app.tools.backend import ToolBackend
from backend.app.tools.schemas import ToolError
from backend.app.tools.logging_shim import ToolCallLogger, default_logger

class BudgetExhausted(Exception):
    pass

class Budget:
    def __init__(self, max_calls: int = 6):
        self.max_calls = max_calls
        self.used = 0
        self._lock = threading.Lock()

    @property
    def remaining(self) -> int:
        with self._lock:
            return max(0, self.max_calls - self.used)

    def can_spend(self) -> bool:
        with self._lock:
            return self.used < self.max_calls

    def spend(self) -> int:
        with self._lock:
            if self.used >= self.max_calls:
                raise BudgetExhausted("Tool call budget exhausted (max 6 calls).")
            self.used += 1
            return self.used

class ToolGateway:
    ALLOWED_TOOLS = {"list_documents", "list_headings", "get_page", "search_keyword"}

    def __init__(
        self,
        backend: ToolBackend,
        doc_id: str | list[str] | set[str],
        budget: Budget | None = None,
        logger: ToolCallLogger | None = None,
        on_event: Callable[[dict[str, Any]], None] | None = None
    ):
        self.backend = backend
        if isinstance(doc_id, str):
            self.allowed_doc_ids = {doc_id}
            self.doc_id = doc_id
        else:
            self.allowed_doc_ids = set(doc_id)
            self.doc_id = sorted(list(self.allowed_doc_ids))[0] if self.allowed_doc_ids else ""
        self.budget = budget or Budget(max_calls=settings.TOOL_BUDGET)
        self.logger = logger or default_logger
        self.on_event = on_event
        self._run_cache: dict[tuple[str, str], Any] = {}
        self._seq = 0

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _emit_event(self, tool_name: str, args: dict[str, Any], purpose: str,
                    status: str, result: Any, result_summary: str, duration_ms: int):
        event = {
            "seq": self._next_seq(),
            "tool": tool_name,
            "args": args,
            "purpose": purpose,
            "status": status,
            "result": result,
            "result_summary": result_summary,
            "duration_ms": duration_ms,
            "calls_used": self.budget.used,
            "calls_remaining": self.budget.remaining
        }
        if self.on_event:
            self.on_event(event)

    def resolve_doc_id(self, raw_id: Any) -> str | None:
        if not raw_id:
            return None
        s = str(raw_id).strip()
        if s in self.allowed_doc_ids:
            return s
        
        sorted_ids = sorted(list(self.allowed_doc_ids))
        m = re.search(r'\b(?:doc(?:ument)?[_\s]*)?([1-9])\b', s, re.IGNORECASE)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(sorted_ids):
                return sorted_ids[idx]
        
        s_low = s.lower()
        for did in self.allowed_doc_ids:
            doc = self.backend.repo.get_document(did)
            if doc:
                title = doc.get("title", "").lower()
                filename = doc.get("filename", "").lower()
                if s_low in title or s_low in filename or title in s_low or filename in s_low:
                    return did
        return None

    def execute(self, tool_name: str, raw_args: dict[str, Any] | None = None, purpose: str = "") -> tuple[bool, Any, str]:
        """
        Executes a tool call through the metered gateway.
        Returns: (success: bool, result_or_error_msg: Any, status: 'ok'|'deduped'|'refused'|'error')
        """
        raw_args = raw_args or {}

        # 1. Allowlist
        if tool_name not in self.ALLOWED_TOOLS:
            msg = f"Unknown tool '{tool_name}'. Allowed: {sorted(list(self.ALLOWED_TOOLS))}"
            self._emit_event(tool_name, raw_args, purpose, "refused", msg, msg, 0)
            return False, msg, "refused"

        # 2. Document scoping and doc_id validation
        clean_args = {}
        if tool_name != "list_documents":
            if len(self.allowed_doc_ids) == 1:
                clean_args["doc_id"] = list(self.allowed_doc_ids)[0]
            else:
                raw_did = raw_args.get("doc_id") or raw_args.get("doc")
                resolved = self.resolve_doc_id(raw_did)
                if resolved:
                    clean_args["doc_id"] = resolved
                elif raw_did and not resolved:
                    msg = f"Forbidden doc_id '{raw_did}'. Allowed in this session: {sorted(list(self.allowed_doc_ids))}"
                    self._emit_event(tool_name, raw_args, purpose, "refused", msg, msg, 0)
                    return False, msg, "refused"
                else:
                    msg = f"Multi-document session requires 'doc_id'. Allowed: {sorted(list(self.allowed_doc_ids))}"
                    self._emit_event(tool_name, raw_args, purpose, "refused", msg, msg, 0)
                    return False, msg, "refused"

        # 3. Schema validation & normalization
        if tool_name == "get_page":
            page_val = raw_args.get("page_number") if "page_number" in raw_args else raw_args.get("page")
            if page_val is None or isinstance(page_val, bool) or not isinstance(page_val, int):
                msg = f"Invalid page_number: must be a plain integer, got {type(page_val).__name__} ({page_val})"
                self._emit_event(tool_name, raw_args, purpose, "refused", msg, msg, 0)
                return False, msg, "refused"
            clean_args["page_number"] = page_val

        elif tool_name == "search_keyword":
            kw = raw_args.get("keyword")
            if not isinstance(kw, str) or len(kw.strip()) < 2 or len(kw.strip()) > 80:
                msg = f"Invalid keyword: must be a string of 2-80 characters, got {kw!r}"
                self._emit_event(tool_name, raw_args, purpose, "refused", msg, msg, 0)
                return False, msg, "refused"
            clean_args["keyword"] = kw.strip()

        # 4. Deduplication
        cache_key = (tool_name, str(sorted(clean_args.items())))
        if cache_key in self._run_cache:
            cached_res = self._run_cache[cache_key]
            summary = self._summarize_result(tool_name, cached_res)
            self._emit_event(tool_name, clean_args, purpose, "deduped", cached_res, f"[Cached] {summary}", 0)
            return True, cached_res, "deduped"

        # 5. Budget check
        if not self.budget.can_spend():
            msg = "Tool call budget exhausted (max 6 calls reached)."
            self._emit_event(tool_name, clean_args, purpose, "refused", msg, msg, 0)
            return False, msg, "refused"

        # 6. Execution via logging wrapper
        start_t = time.perf_counter()
        try:
            fn = getattr(self.backend, tool_name)
            # Spend budget right before execution
            self.budget.spend()
            if tool_name == "list_documents":
                result = self.logger(tool_name, clean_args, lambda: self.backend.list_documents(doc_ids=list(self.allowed_doc_ids)))
            else:
                result = self.logger(tool_name, clean_args, fn)
            duration_ms = int((time.perf_counter() - start_t) * 1000)
            summary = self._summarize_result(tool_name, result)
            self._run_cache[cache_key] = result
            self._emit_event(tool_name, clean_args, purpose, "ok", result, summary, duration_ms)
            return True, result, "ok"

        except ToolError as te:
            duration_ms = int((time.perf_counter() - start_t) * 1000)
            self._emit_event(tool_name, clean_args, purpose, "error", te.message, te.message, duration_ms)
            return False, te.message, "error"
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_t) * 1000)
            self._emit_event(tool_name, clean_args, purpose, "error", str(e), str(e), duration_ms)
            return False, str(e), "error"

    def _summarize_result(self, tool_name: str, result: Any) -> str:
        if tool_name == "list_documents":
            return f"{len(result)} document(s)"
        elif tool_name == "list_headings":
            return f"{len(result)} headings"
        elif tool_name == "get_page":
            txt = result.get("text", "")
            return f"{len(txt)} chars"
        elif tool_name == "search_keyword":
            return f"pages {result}"
        return str(result)[:50]
