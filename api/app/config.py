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
    LOG_LEVEL: str = "INFO"

    # ── Database ──────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ciotx:ciotx@postgres:5432/ciotx"
    DB_PASSWORD: str = ""
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # ── Redis ─────────────────────────────────
    REDIS_URL: str = "redis://:ciotx@redis:6379"
    REDIS_PASSWORD: str = ""

    # ── JWT / Auth ────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_TIME_COST: int = 3
    ARGON2_PARALLELISM: int = 4
    INTERNAL_API_KEY: str = "change-me"

    # ── LLM Providers ─────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    CUSTOM_API_KEY: str = ""
    CUSTOM_BASE_URL: str = ""
    CIOTX_RELAY_URL: str = ""
    LLM_PROVIDER: str = "auto"
    LLM_FALLBACK: str = "deepseek,anthropic,openai"

    # ── LLM Tuning ────────────────────────────
    LLM_TIMEOUT_SEC: int = 120
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_MAX_LINES_PER_FILE: int = 500

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
    TRIAL_DAYS: int = 7
    TRIAL_SCAN_LIMIT: int = 10
    STARTER_SCAN_LIMIT: int = 20
    STARTER_PRICE_MONTHLY: int = 39900
    STARTER_PRICE_ANNUAL: int = 399900
    PRO_PRICE_MONTHLY: int = 149900
    PRO_PRICE_ANNUAL: int = 1499900

    # ── Scan Engine ───────────────────────────
    SCAN_MAX_FILE_SIZE: int = 10485760
    CLI_PKCE_POLL_INTERVAL: int = 2
    CLI_PKCE_TIMEOUT: int = 600

    # ── Rate Limiting ─────────────────────────
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_SIGNUP: str = "3/hour"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DEV_MODE:
            errors = []
            if self.SECRET_KEY == "change-me-in-production":
                errors.append("SECRET_KEY must be changed from default. Generate: openssl rand -hex 32")
            if self.INTERNAL_API_KEY == "change-me":
                errors.append("INTERNAL_API_KEY must be changed from default.")
            if not self.GITHUB_WEBHOOK_SECRET:
                errors.append("GITHUB_WEBHOOK_SECRET is required in production.")
            if not self.RAZORPAY_WEBHOOK_SECRET:
                errors.append("RAZORPAY_WEBHOOK_SECRET is required in production.")
            if not (self.DEEPSEEK_API_KEY or self.OPENAI_API_KEY or self.ANTHROPIC_API_KEY or self.CUSTOM_API_KEY):
                errors.append("At least one LLM API key is required (DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or CUSTOM_API_KEY).")
            if errors:
                raise RuntimeError("Production configuration errors:\n- " + "\n- ".join(errors))


settings = Settings()
