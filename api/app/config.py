"""
CIOTX API — Configuration
All settings from environment variables. No hardcoded values.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────
    APP_NAME: str = "CIOTX"
    APP_VERSION: str = "0.1.0"
    API_BASE_URL: str = "http://localhost:8000"
    DASHBOARD_URL: str = "http://localhost:3000"
    DEV_MODE: bool = True
    DEV_AUTO_PLAN: str = "pro"

    # ── Database ──────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ciotx:ciotx@postgres:5432/ciotx"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # ── Redis ─────────────────────────────────
    REDIS_URL: str = "redis://:ciotx@redis:6379"

    # ── JWT / Auth ────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ARGON2_MEMORY_COST: int = 65536  # 64 MB
    ARGON2_TIME_COST: int = 3
    ARGON2_PARALLELISM: int = 4

    # ── LLM Providers ─────────────────────────
    DEEPSEEK_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CUSTOM_API_KEY: str = ""
    CUSTOM_BASE_URL: str = ""
    LLM_PROVIDER: str = "auto"
    LLM_FALLBACK: str = "deepseek,anthropic,openai"

    # ── GitHub ────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_APP_ID: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_PRIVATE_KEY_PATH: str = ""

    # ── Billing ───────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── Internal ──────────────────────────────
    INTERNAL_API_KEY: str = "change-me"

    # ── Rate Limiting ─────────────────────────
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_SIGNUP: str = "3/hour"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
