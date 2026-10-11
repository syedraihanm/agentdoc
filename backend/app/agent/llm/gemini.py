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
    # Strip markdown code blocks ```json ... ```
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()

class GeminiClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL or "gemini-flash-latest"

    def complete_json(
        self,
        system: str,
        messages: list[dict[str, str]],
        schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 2000,
        timeout: int = 60
    ) -> tuple[T, str, dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Build contents
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        # Guide model with exact JSON schema
        schema_prompt = f"{system}\n\nOUTPUT MUST CONFORM EXACTLY TO THIS JSON SCHEMA:\n{json.dumps(schema.model_json_schema())}"

        payload = {
            "systemInstruction": {
                "parts": [{"text": schema_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        start_t = time.perf_counter()
        raw_text = ""
        last_error = None

        # Auto-fallback models if primary model is invalid or 503 (overloaded / no capacity)
        fallback_chain = [m for m in [self.model, "gemini-flash-lite-latest"] if m]
        # De-duplicate while preserving order
        models_to_try = []
        for m in fallback_chain:
            if m not in models_to_try:
                models_to_try.append(m)

        for m_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={self.api_key}"
            for attempt in range(2):
                try:
                    with httpx.Client(timeout=timeout) as client:
                        resp = client.post(url, json=payload)
                        resp.raise_for_status()
                        data = resp.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        break
                except Exception as e:
                    last_error = e
                    time.sleep(1.0)
            if raw_text:
                break
        else:
            raise RuntimeError(f"Gemini API request failed after retries: {last_error}")

        duration_ms = int((time.perf_counter() - start_t) * 1000)
        usage = {"duration_ms": duration_ms, "model": self.model}

        clean_json = extract_json(raw_text)
        try:
            parsed = schema.model_validate_json(clean_json)
            return parsed, raw_text, usage
        except (json.JSONDecodeError, ValidationError) as parse_err:
            # 1 repair retry
            repair_prompt = f"The following JSON was invalid for schema {schema.__name__}:\n{clean_json}\n\nError: {str(parse_err)}\nReturn ONLY the corrected JSON:"
            payload["contents"].append({
                "role": "user",
                "parts": [{"text": repair_prompt}]
            })
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    repair_raw = data["candidates"][0]["content"]["parts"][0]["text"]
                    repaired_clean = extract_json(repair_raw)
                    parsed = schema.model_validate_json(repaired_clean)
                    usage["repaired"] = True
                    return parsed, repair_raw, usage
            except Exception:
                raise parse_err