import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.agent.runner import AgentLimitError, run_agent
from app.api.dependencies import get_provider
from app.api.schemas import ChatRequest, ChatResponse
from app.config import get_settings
from app.llm.base import LLMProvider


logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    provider: Annotated[LLMProvider, Depends(get_provider)],
) -> ChatResponse:
    settings = get_settings()

    logger.info("Chat endpoint: entering agent runner")

    try:
        result = await asyncio.wait_for(
            run_agent(
                provider=provider,
                user_message=body.message,
                max_tool_calls=settings.agent_max_tool_calls,
            ),
            timeout=60,
        )

    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="The investigation exceeded its time limit.",
        ) from exc

    except AgentLimitError as exc:
        raise HTTPException(
            status_code=503,
            detail="The investigation reached its tool-call limit.",
        ) from exc

    except Exception as exc:
        logger.error(
            "Agent request failed: %s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="The AI investigation failed. Please try again.",
        ) from exc

    return ChatResponse(
        answer=result.text,
        usage=result.usage,
    )
