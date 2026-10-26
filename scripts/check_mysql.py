import sys

import pymysql

from app.db import mysql_connection


def main() -> None:
    try:
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        1 AS connection_ok,
                        DATABASE() AS database_name,
                        @@session.time_zone AS session_timezone
                    """
                )

                print("Connection successful:")
                print(cursor.fetchone())

                cursor.execute(
                    """
                    SELECT TABLE_SCHEMA, TABLE_NAME
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME IN (%s, %s)
                    ORDER BY TABLE_NAME
                    """,
                    ("whatsapp_meta", "global_campaigner"),
                )

                tables = cursor.fetchall()

                print("\nMatching tables:")

                if not tables:
                    print("Neither table was found or visible.")
                else:
                    for table in tables:
                        print(
                            f"{table['TABLE_SCHEMA']}."
                            f"{table['TABLE_NAME']}"
                        )

    except pymysql.MySQLError as exc:
        code = exc.args[0] if exc.args else "unknown"
        print(f"MySQL check failed. Error code: {code}")
        sys.exit(1)

    except ValueError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()