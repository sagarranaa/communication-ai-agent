from abc import ABC, abstractmethod
from typing import Any

from app.llm.schemas import Message, ModelTurn, ToolDefinition


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        *,
        provider_state: dict[str, Any] | None = None,
    ) -> ModelTurn:
        """Ask the model for an answer or tool calls."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the provider's network client."""
        ...