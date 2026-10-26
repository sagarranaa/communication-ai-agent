from typing import Any

from openai import AsyncOpenAI

from app.config import Settings
from app.llm.base import LLMProvider
from app.llm.schemas import (
    Message,
    ModelTurn,
    TokenUsage,
    ToolCall,
    ToolDefinition,
)


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: Settings):
        api_key = settings.openai_api_key.get_secret_value().strip()

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing in .env")

        if not settings.llm_model.strip():
            raise ValueError("LLM_MODEL is missing in .env")

        self.model = settings.llm_model.strip()

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )

    @staticmethod
    def _serialize_message(message: Message) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "role": message.role,
            "content": message.content,
        }

        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": call.arguments_json,
                    },
                }
                for call in message.tool_calls
            ]

        if message.role == "tool":
            if not message.tool_call_id:
                raise ValueError("Tool results require a tool_call_id")

            payload["tool_call_id"] = message.tool_call_id

        return payload

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        *,
        provider_state: dict[str, Any] | None = None,
    ) -> ModelTurn:
        if provider_state:
            raise ValueError(
                "This adapter uses message history, not provider state."
            )

        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                self._serialize_message(message)
                for message in messages
            ],
            "max_completion_tokens": 2048,
        }

        if tools:
            request["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]

            request["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(
            **request
        )

        if not response.choices:
            raise RuntimeError("OpenAI returned no response choices")

        choice = response.choices[0]

        if choice.finish_reason not in {"stop", "tool_calls"}:
            raise RuntimeError(
                "OpenAI response did not complete normally: "
                f"{choice.finish_reason}"
            )

        reply = choice.message

        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments_json=call.function.arguments,
            )
            for call in (reply.tool_calls or [])
        ]

        if not calls and not (reply.content or "").strip():
            raise RuntimeError("OpenAI returned an empty response")

        usage = response.usage

        return ModelTurn(
            text=reply.content,
            tool_calls=calls,
            usage=TokenUsage(
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            ),
        )

    async def close(self) -> None:
        await self.client.close()