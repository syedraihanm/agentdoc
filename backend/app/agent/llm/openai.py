import json
import re
import time
from typing import Type, TypeVar, Any
import httpx
from pydantic import BaseModel, ValidationError
from backend.app.config import settings
from backend.app.agent.llm.base import LLMClient

T = TypeVar("T", bound=BaseModel)

def extract_json(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()

class OpenAIClient(LLMClient):
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.model = model or settings.LLM_MODEL or "gpt-4o-mini"

    def complete_json(
        self,
        system: str,
        messages: list[dict[str, str]],
        schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 2000,
        timeout: int = 60
    ) -> tuple[T, str, dict[str, Any]]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        full_messages = [{"role": "system", "content": system}] + messages
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        start_t = time.perf_counter()
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]

        clean = extract_json(raw_text)
        parsed = schema.model_validate_json(clean)
        usage = {"duration_ms": int((time.perf_counter() - start_t) * 1000), "model": self.model}
        return parsed, raw_text, usage

class OllamaClient(LLMClient):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.LLM_BASE_URL or "http://localhost:11434").rstrip("/")
        self.model = model or settings.LLM_MODEL or "llama3.2"

    def complete_json(
        self,
        system: str,
        messages: list[dict[str, str]],
        schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 2000,
        timeout: int = 60
    ) -> tuple[T, str, dict[str, Any]]:
        url = f"{self.base_url}/api/chat"
        full_messages = [{"role": "system", "content": system}] + messages
        payload = {
            "model": self.model,
            "messages": full_messages,
            "format": "json",
            "stream": False,
            "options": {"temperature": temperature}
        }
        start_t = time.perf_counter()
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["message"]["content"]
        clean = extract_json(raw_text)
        parsed = schema.model_validate_json(clean)
        usage = {"duration_ms": int((time.perf_counter() - start_t) * 1000), "model": self.model}
        return parsed, raw_text, usage