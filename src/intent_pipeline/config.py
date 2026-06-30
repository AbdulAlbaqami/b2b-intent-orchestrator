"""Global configuration loaded from .env. Secrets are never hard-coded."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Global
    dry_run: bool = True  # when True, all external calls return mock data
    daily_email_limit: int = 5
    enrichment_score_threshold: float = 0.85

    # Secrets (filled in .env; blank by default)
    job_board_api_key: str = ""
    apollo_api_key: str = ""
    anthropic_api_key: str = ""
    admin_email: str = ""


settings = Settings()
