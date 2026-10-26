import argparse
import json
from datetime import date

import pymysql

from app.repositories.messages import get_message_summary


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        required=True,
        type=date.fromisoformat,
        help="Inclusive start date: YYYY-MM-DD",
    )

    parser.add_argument(
        "--end",
        required=True,
        type=date.fromisoformat,
        help="Exclusive end date: YYYY-MM-DD",
    )

    args = parser.parse_args()

    try:
        result = get_message_summary(
            start_date=args.start,
            end_date=args.end,
        )

    except ValueError as exc:
        parser.exit(1, f"Configuration/input error: {exc}\n")

    except pymysql.MySQLError as exc:
        code = exc.args[0] if exc.args else "unknown"
        parser.exit(1, f"MySQL query failed. Error code: {code}\n")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()