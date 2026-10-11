from backend.app.config import settings
from backend.app.storage.repo import Repo
from backend.app.storage.db import init_db
from backend.app.agent.llm.base import LLMClient
from backend.app.agent.llm.gemini import GeminiClient
from backend.app.agent.llm.openai import OpenAIClient, OllamaClient
from backend.app.agent.llm.fake import FakeLLM

# Ensure DB initialized
init_db()
repo = Repo()

def get_repo() -> Repo:
    return repo

def get_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini":
        return GeminiClient()
    elif provider == "openai":
        return OpenAIClient()
    elif provider == "ollama":
        return OllamaClient()
    elif provider == "fake":
        return FakeLLM()
    # Default to Gemini if key available, else OpenAI
    if settings.GOOGLE_API_KEY:
        return GeminiClient()
    elif settings.OPENAI_API_KEY:
        return OpenAIClient()
    return GeminiClient()