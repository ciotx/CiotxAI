"""
CIOTX API — Auth Service
argon2id password hashing, JWT issuance/verification, token rotation with reuse detection.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from jose import JWTError, jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import ApiToken, User

ph = PasswordHasher(
    memory_cost=settings.ARGON2_MEMORY_COST,
    time_cost=settings.ARGON2_TIME_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

# ── Password Hashing ─────────────────────────

def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        ph.verify(password_hash, password)
        if ph.check_needs_rehash(password_hash):
            return True  # caller should rehash but login succeeds
        return True
    except (VerificationError, InvalidHashError):
        return False


# ── JWT ──────────────────────────────────────

def create_access_token(user_id: str, email: str, plan: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "plan": plan,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": secrets.token_hex(16),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── Refresh Token Management ─────────────────

async def store_refresh_token(
    db: AsyncSession, user_id: str, family_id: str | None = None
) -> str:
    """Create and store a refresh token. Returns the raw token (not the hash)."""
    raw_token = create_refresh_token()
    token_hash = hash_token(raw_token)
    family = family_id or str(uuid.uuid4())

    db_token = ApiToken(
        user_id=user_id,
        token_hash=token_hash,
        name="refresh",
        token_type="refresh",
        family_id=family,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_token)
    await db.flush()
    return raw_token


async def rotate_refresh_token(
    db: AsyncSession, raw_token: str
) -> tuple[str, str, str] | None:
    """
    Rotate a refresh token. Returns (new_raw_token, user_id, family_id) or None if invalid.
    If the token has already been used, the ENTIRE family is invalidated (reuse detection).
    """
    token_hash = hash_token(raw_token)

    result = await db.execute(
        select(ApiToken).where(ApiToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if db_token is None:
        return None

    # Check expiry
    if db_token.expires_at < datetime.now(timezone.utc):
        return None

    # REUSE DETECTION: if this token was already used, someone stole the family
    if db_token.used:
        await db.execute(
            update(ApiToken)
            .where(ApiToken.family_id == db_token.family_id)
            .values(used=True)
        )
        await db.flush()
        return None

    # Mark current token as used
    db_token.used = True
    db_token.last_used_at = datetime.now(timezone.utc)

    # Issue new token in the same family
    new_raw_token = create_refresh_token()
    new_token_hash = hash_token(new_raw_token)

    new_db_token = ApiToken(
        user_id=db_token.user_id,
        token_hash=new_token_hash,
        name="refresh",
        token_type="refresh",
        family_id=db_token.family_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_db_token)
    await db.flush()

    return new_raw_token, db_token.user_id, db_token.family_id


async def revoke_token_family(db: AsyncSession, family_id: str) -> None:
    """Revoke all tokens in a family."""
    await db.execute(
        update(ApiToken)
        .where(ApiToken.family_id == family_id)
        .values(used=True)
    )
    await db.flush()


# ── User Helpers ─────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ── Email Verification (dev mode: auto-verify) ──

VERIFICATION_CODES: dict[str, tuple[str, datetime]] = {}


def generate_verification_code(email: str) -> str:
    """Generate a 6-digit verification code."""
    if settings.DEV_MODE:
        code = "000000"
    else:
        code = f"{secrets.randbelow(1000000):06d}"
    VERIFICATION_CODES[email] = (code, datetime.now(timezone.utc) + timedelta(minutes=10))
    return code


def verify_email_code(email: str, code: str) -> bool:
    """Verify a 6-digit code."""
    stored = VERIFICATION_CODES.get(email)
    if stored is None:
        return False
    stored_code, expires_at = stored
    if datetime.now(timezone.utc) > expires_at:
        del VERIFICATION_CODES[email]
        return False
    if stored_code != code:
        return False
    del VERIFICATION_CODES[email]
    return True
