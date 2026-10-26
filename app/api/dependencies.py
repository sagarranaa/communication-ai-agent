from typing import cast

from fastapi import Request

from app.llm.base import LLMProvider


def get_provider(request: Request) -> LLMProvider:
    return cast(
        LLMProvider,
        request.app.state.llm_provider,
    )