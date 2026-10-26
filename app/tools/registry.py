import json
import logging
from datetime import date
from typing import Any

import pymysql
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.llm.schemas import ToolDefinition
from app.repositories.messages import (
    get_failure_breakdown,
    get_message_summary,
)


logger = logging.getLogger("uvicorn.error")


class StatusLookupArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status_code: int


class DateRangeArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    start_date: date = Field(
        description="Inclusive start date in YYYY-MM-DD format."
    )
    end_date: date = Field(
        description=(
            "Exclusive end date in YYYY-MM-DD format. "
            "The range must be between 1 and 31 days."
        )
    )


WHATSAPP_STATUSES = {
    1: "submitted",
    2: "sent",
    3: "delivered",
    4: "read",
    9: "failed",
}


TOOL_DEFINITIONS = [
    ToolDefinition(
        name="lookup_whatsapp_status",
        description=(
            "Look up a numeric whatsapp_meta message status. "
            "Does not apply to global_campaigner statuses."
        ),
        parameters=StatusLookupArguments.model_json_schema(),
    ),
    ToolDefinition(
        name="get_whatsapp_message_summary",
        description=(
            "Query current WhatsApp message status counts for the "
            "backend-configured development account. "
            "Filters by created_at with inclusive start and exclusive end. "
            "Maximum range: 31 days. "
            "Does not provide failure reasons or campaign-specific results."
        ),
        parameters=DateRangeArguments.model_json_schema(),
    ),
    ToolDefinition(
        name="get_whatsapp_failure_breakdown",
        description=(
            "Query recorded error codes and reasons for WhatsApp messages "
            "with current status 9 (failed), for the fixed backend account. "
            "Returns total failures and the ten largest error groups. "
            "Filters by created_at with inclusive start and exclusive end. "
            "Maximum range: 31 days. "
            "Use after a summary shows failures when investigating why "
            "messages failed. Recorded reasons are not verified root causes."
        ),
        parameters=DateRangeArguments.model_json_schema(),
    ),
]


def execute_tool(
    name: str,
    arguments_json: str,
) -> dict[str, Any]:
    try:
        if name == "lookup_whatsapp_status":
            arguments = StatusLookupArguments.model_validate_json(
                arguments_json
            )

            meaning = WHATSAPP_STATUSES.get(arguments.status_code)

            return {
                "ok": True,
                "status_code": arguments.status_code,
                "meaning": meaning or "unknown",
                "mapping_known": meaning is not None,
                "source": "Provided whatsapp_meta.status schema comment",
                "live_database_query": False,
            }

        database_tools = {
            "get_whatsapp_message_summary": get_message_summary,
            "get_whatsapp_failure_breakdown": get_failure_breakdown,
        }

        if name in database_tools:
            arguments = DateRangeArguments.model_validate_json(
                arguments_json
            )

            result = database_tools[name](
                start_date=arguments.start_date,
                end_date=arguments.end_date,
            )

            return {
                "ok": True,
                "data": result,
            }

        return {
            "ok": False,
            "error": "Unknown tool.",
        }

    except ValidationError:
        return {
            "ok": False,
            "error": (
                "Invalid arguments. Follow the tool schema. "
                "Dates must be YYYY-MM-DD strings."
            ),
        }

    except ValueError as exc:
        return {
            "ok": False,
            "error": str(exc),
        }

    except pymysql.MySQLError as exc:
        code = exc.args[0] if exc.args else "unknown"

        logger.error(
            "Database tool failed; MySQL code=%s",
            code,
        )

        return {
            "ok": False,
            "error": (
                "The database query failed. "
                "No results were retrieved."
            ),
        }


def serialize_tool_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False)