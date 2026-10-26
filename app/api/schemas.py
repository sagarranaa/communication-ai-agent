from pydantic import BaseModel, ConfigDict, Field

from app.llm.schemas import TokenUsage


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    message: str = Field(
        min_length=1,
        max_length=4000,
    )


class ChatResponse(BaseModel):
    answer: str
    usage: TokenUsage