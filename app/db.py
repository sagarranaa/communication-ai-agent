from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from app.config import get_settings


@contextmanager
def mysql_connection() -> Iterator[Connection]:
    settings = get_settings()

    if not settings.mysql_user or not settings.mysql_database:
        raise ValueError(
            "Set MYSQL_USER and MYSQL_DATABASE in .env"
        )

    tls_options = {}

    if settings.mysql_ssl_ca:
        tls_options = {
            "ssl_ca": settings.mysql_ssl_ca,
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        }

    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password.get_secret_value(),
        database=settings.mysql_database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=settings.mysql_connect_timeout_seconds,
        read_timeout=settings.mysql_read_timeout_seconds,
        write_timeout=settings.mysql_read_timeout_seconds,
        autocommit=False,
        **tls_options,
    )

    try:
        yield connection
    finally:
        connection.close()