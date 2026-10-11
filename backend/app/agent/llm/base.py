from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMClient(ABC):
    @abstractmethod
    def complete_json(
        self,
        system: str,
        messages: list[dict[str, str]],
        schema: Type[T],
        temperature: float = 0.0,
        max_tokens: int = 1500,
        timeout: int = 60
    ) -> tuple[T, str, dict[str, Any]]:
        """
        Executes an LLM call and returns (parsed_schema_instance, raw_text, usage_info).
        """
        pass