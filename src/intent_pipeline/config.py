"""Global configuration.

Two different kinds of value live here, and the split is deliberate (ADR-004):

- ``Settings`` — *deployment configuration*: values that legitimately differ per
  machine or per run, loaded from ``.env``. Secrets are never hard-coded.
- Module constants — *business contract*: values the test suite must be able to
  guarantee. These are deliberately NOT ``Settings`` fields, because
  ``pydantic-settings`` resolves any environment variable matching a field name.
  As a field, a stray ``ENRICHMENT_SCORE_THRESHOLD=0.5`` in a ``.env`` would
  silently disable a business rule (Hard Rules 2 and 3) with no test failure.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Business contract (ADR-004): code, not configuration -------------------
# Module constants, not Settings fields: no environment variable may override a
# business rule the test suite is meant to guarantee.
ENRICHMENT_SCORE_THRESHOLD: float = 0.85  # Hard Rule 2 — enrichment gate
DAILY_EMAIL_LIMIT: int = 5  # Hard Rule 3 — advisory emails per UTC day


class Settings(BaseSettings):
    """Deployment configuration, loaded from `.env` (see `.env.example`)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Global
    dry_run: bool = True  # when True, all external calls return mock data
    database_path: str = "data/intent_pipeline.db"
    admin_email: str = ""

    # Layer 1 — Adzuna authenticates with a paired app id + app key
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # Layer 2.5 — enrichment provider (F2: mock through V1)
    apollo_api_key: str = ""

    # Layer 4 — LLM drafter
    anthropic_api_key: str = ""


settings = Settings()
