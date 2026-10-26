from app.config import Settings
from app.llm.base import LLMProvider


def create_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "groq":
        from app.llm.groq_provider import GroqProvider

        return GroqProvider(settings)

    if settings.llm_provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(settings)

    raise ValueError(
        f"Unsupported provider: {settings.llm_provider}"
    )