from app.db import mysql_connection


def main() -> None:
    with mysql_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_NAME IN (%s, %s)
                ORDER BY TABLE_SCHEMA, TABLE_NAME
                """,
                ("whatsapp_meta", "global_campaigner"),
            )

            tables = cursor.fetchall()

            if not tables:
                print("No matching tables are visible to this account.")
                return

            print("Visible matching tables:")

            for table in tables:
                print(
                    f"{table['TABLE_SCHEMA']}."
                    f"{table['TABLE_NAME']}"
                )


if __name__ == "__main__":
    main()