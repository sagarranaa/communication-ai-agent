import asyncio
import json
import logging

from app.agent.runner import run_agent
from app.config import get_settings
from app.llm.factory import create_provider


EXPECTED_DATES = {
    "start_date": "2023-08-05",
    "end_date": "2023-08-06",
}


def build_fixture_executor():
    calls = []

    def fixture_executor(name: str, arguments_json: str) -> dict:
        try:
            arguments = json.loads(arguments_json)
        except json.JSONDecodeError:
            return {
                "ok": False,
                "error": "Arguments must be valid JSON.",
            }

        calls.append({
            "name": name,
            "arguments": arguments,
        })

        if arguments != EXPECTED_DATES:
            return {
                "ok": False,
                "error": (
                    "This fixture accepts only start_date=2023-08-05 "
                    "and end_date=2023-08-06."
                ),
            }

        common = {
            "account": "synthetic_test_account",
            "source": "synthetic_fixture",
            "start_inclusive": "2023-08-05",
            "end_exclusive": "2023-08-06",
            "live_database_query": False,
            "synthetic": True,
        }

        if name == "get_whatsapp_message_summary":
            return {
                "ok": True,
                "data": {
                    **common,
                    "total_matching_records": 10,
                    "counts_by_current_status": [
                        {
                            "status_code": 4,
                            "status": "read",
                            "count": 7,
                        },
                        {
                            "status_code": 9,
                            "status": "failed",
                            "count": 3,
                        },
                    ],
                },
            }

        if name == "get_whatsapp_failure_breakdown":
            return {
                "ok": True,
                "data": {
                    **common,
                    "failure_status_code": 9,
                    "total_failed_records": 3,
                    "top_error_groups": [
                        {
                            "error_code": "TEST_TIMEOUT",
                            "error_reason": (
                                "Synthetic example: upstream request "
                                "timed out."
                            ),
                            "count": 2,
                        },
                        {
                            "error_code": None,
                            "error_reason": None,
                            "count": 1,
                        },
                    ],
                    "records_in_returned_groups": 3,
                    "returned_group_limit": 10,
                },
            }

        return {
            "ok": False,
            "error": "This tool is not available in this fixture.",
        }

    return fixture_executor, calls


async def main() -> None:
    settings = get_settings()
    provider = create_provider(settings)
    fixture_executor, calls = build_fixture_executor()

    try:
        result = await run_agent(
            provider=provider,
            user_message=(
                "Why did my WhatsApp messages fail on August 5, 2023?"
            ),
            max_tool_calls=settings.agent_max_tool_calls,
            tool_executor=fixture_executor,
            evidence_note=(
                "This is an evaluation using synthetic data. "
                "Clearly label your final answer as a synthetic test. "
                "No live customer records are being queried. "
                "Use the same investigation workflow as normal."
            ),
        )
    finally:
        await provider.close()

    print("\nTOOL CALLS:")
    print(json.dumps(calls, indent=2))

    print("\nAGENT ANSWER:")
    print(result.text)

    expected_names = [
        "get_whatsapp_message_summary",
        "get_whatsapp_failure_breakdown",
    ]
    actual_names = [call["name"] for call in calls]

    if actual_names != expected_names:
        raise SystemExit(
            "\nFAIL: Expected summary followed by failure breakdown."
        )

    if any(call["arguments"] != EXPECTED_DATES for call in calls):
        raise SystemExit("\nFAIL: Incorrect date arguments.")

    print("\nPASS: Correct tool order and date arguments.")
    print("Review the answer against the expected facts below:")
    print("- Clearly identified as synthetic data.")
    print("- 10 records total, including 3 failures.")
    print("- 2 failures have a recorded synthetic timeout reason.")
    print("- 1 failure has no recorded error details.")
    print("- No claim that a root cause has been independently proven.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())