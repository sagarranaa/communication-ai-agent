from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Communication AI Service"
    app_env: Literal["development", "test", "production"] = "development"
    dev_account_username: str = ""

    # AI provider
    llm_provider: Literal["groq", "openai"] = "groq"
    llm_model: str = ""

    groq_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")

    llm_timeout_seconds: float = Field(default=30, gt=0)
    agent_max_tool_calls: int = Field(default=8, ge=1, le=30)

    # MySQL connection
    mysql_host: str = "127.0.0.1"
    mysql_port: int = Field(default=3306, ge=1, le=65535)
    mysql_user: str = ""
    mysql_password: SecretStr = SecretStr("")
    mysql_database: str = ""

    # Database locations of the business tables
    mysql_campaign_schema: str = "Main"
    mysql_whatsapp_schema: str = "login_db"

    # MySQL connection options
    mysql_connect_timeout_seconds: int = Field(default=10, ge=1)
    mysql_read_timeout_seconds: int = Field(default=15, ge=1)
    mysql_ssl_ca: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()