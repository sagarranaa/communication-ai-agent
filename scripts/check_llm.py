import asyncio

from app.config import get_settings
from app.llm.factory import create_provider
from app.llm.schemas import Message


async def main() -> None:
    settings = get_settings()
    provider = create_provider(settings)

    try:
        print(f"Provider: {settings.llm_provider}")
        print(f"Model: {settings.llm_model}")
        print("Sending request...")

        result = await provider.generate(
            messages=[
                Message(
                    role="system",
                    content=(
                        "You are a concise technical tutor. "
                        "Explain concepts in simple language."
                    ),
                ),
                Message(
                    role="user",
                    content=(
                        "In two sentences, explain how an AI agent "
                        "uses tools. Do not claim to have database access."
                    ),
                ),
            ],
            tools=[],
        )

        print("\nAI response:")
        print(result.text)

        print("\nToken usage:")
        print(f"Input: {result.usage.input_tokens}")
        print(f"Output: {result.usage.output_tokens}")

    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())