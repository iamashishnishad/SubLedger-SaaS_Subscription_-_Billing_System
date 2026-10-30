from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SubLedger"
    database_url: str = "sqlite:///./subledger.db"
    sql_echo: bool = False
    # Number of days after the billing period starts that an invoice is due.
    invoice_due_days: int = 7
    default_currency: str = "INR"


@lru_cache
def get_settings() -> Settings:
    return Settings()
