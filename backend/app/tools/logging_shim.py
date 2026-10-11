import json
import time
from pathlib import Path
from typing import Callable, Any, Protocol
from datetime import datetime, timezone
from backend.app.config import settings

class ToolCallLogger(Protocol):
    def __call__(self, tool_name: str, args: dict[str, Any], fn: Callable[..., Any]) -> Any:
        ...

class DefaultToolCallLogger:
    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or (settings.TRACES_DIR / "tool_calls.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.executed_calls_count = 0

    def __call__(self, tool_name: str, args: dict[str, Any], fn: Callable[..., Any]) -> Any:
        start_t = time.perf_counter()
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            result = fn(**args)
            duration_ms = int((time.perf_counter() - start_t) * 1000)
            self.executed_calls_count += 1
            entry = {
                "timestamp": timestamp,
                "tool": tool_name,
                "args": args,
                "duration_ms": duration_ms,
                "status": "success"
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            return result
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_t) * 1000)
            entry = {
                "timestamp": timestamp,
                "tool": tool_name,
                "args": args,
                "duration_ms": duration_ms,
                "status": "error",
                "error": str(e)
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            raise

# Global default logger instance
default_logger = DefaultToolCallLogger()
