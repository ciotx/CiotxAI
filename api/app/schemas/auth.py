"""
CIOTX API — Auth Schemas
Pydantic models for all auth request/response types.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CliInitRequest(BaseModel):
    code_challenge: str = Field(min_length=43, max_length=128)


class CliTokenRequest(BaseModel):
    device_code: str
    code_verifier: str = Field(min_length=43, max_length=128)


# ── Response Schemas ─────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes


class CliInitResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int = 600  # 10 minutes


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    avatar_url: str | None
    email_verified: bool
    plan: str
    plan_status: str
    trial_ends_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    dev_mode: bool
