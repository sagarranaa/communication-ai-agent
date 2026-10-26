from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.config import get_settings
from app.llm.factory import create_provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    provider = create_provider(settings)

    app.state.llm_provider = provider

    try:
        yield
    finally:
        await provider.close()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router)


@app.get("/health/live")
async def health():
    return {
        "status": "ok",
        "service": "communication-ai-service",
    }