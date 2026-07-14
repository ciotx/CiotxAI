"""
CIOTX — Redis-backed ephemeral state with in-memory fallback.
Replaces module-level dicts for multi-replica safety.
"""

import hashlib
import hmac
import secrets
import time

import redis.asyncio as aioredis

from app.config import settings


class StateStore:
    """Redis-backed store with TTL. Falls back to in-memory dict in dev/if Redis down."""

    def __init__(self, prefix: str, ttl_seconds: int = 600):
        self.prefix = prefix
        self.ttl = ttl_seconds
        self._redis = None
        self._fallback: dict[str, tuple[str, float]] = {}

    async def _get_redis(self):
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL)
            except Exception:
                self._redis = False  # Mark as unavailable
        return self._redis if self._redis is not False else None

    async def set(self, key: str, value: str) -> None:
        redis = await self._get_redis()
        if redis:
            await redis.setex(f"{self.prefix}:{key}", self.ttl, value)
        else:
            self._fallback[key] = (value, time.time() + self.ttl)

    async def pop(self, key: str) -> str | None:
        # Clean expired fallback entries
        now = time.time()
        self._fallback = {k: v for k, v in self._fallback.items() if v[1] > now}

        redis = await self._get_redis()
        if redis:
            val = await redis.get(f"{self.prefix}:{key}")
            if val:
                await redis.delete(f"{self.prefix}:{key}")
                return val.decode() if isinstance(val, bytes) else val
            return None
        else:
            entry = self._fallback.pop(key, None)
            return entry[0] if entry else None

    async def exists(self, key: str) -> bool:
        redis = await self._get_redis()
        if redis:
            return bool(await redis.exists(f"{self.prefix}:{key}"))
        now = time.time()
        entry = self._fallback.get(key)
        return entry is not None and entry[1] > now


# Global instances (created at import time, connected lazily)
oauth_states = StateStore("oauth", ttl_seconds=600)
gh_oauth_states = StateStore("gh_oauth", ttl_seconds=600)
reset_tokens = StateStore("reset", ttl_seconds=3600)
verification_codes = StateStore("verify", ttl_seconds=600)


def generate_verification_code(email: str) -> str:
    """Generate a 6-digit code and store in Redis-backed state."""
    code = "000000" if settings.DEV_MODE else f"{secrets.randbelow(1000000):06d}"
    import asyncio
    try:
        asyncio.get_running_loop().create_task(verification_codes.set(email, code))
    except RuntimeError:
        verification_codes._fallback[email] = (code, time.time() + 600)
    return code


def verify_email_code(email: str, code: str) -> bool:
    """Verify a 6-digit code. Returns True if valid."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # Can't await in sync function — check fallback only for sync callers
        entry = verification_codes._fallback.get(email)
        if entry and entry[0] == code and entry[1] > time.time():
            del verification_codes._fallback[email]
            return True
        return False
    except RuntimeError:
        return False


async def verify_email_code_async(email: str, code: str) -> bool:
    """Async version for use in route handlers."""
    stored = await verification_codes.pop(email)
    return stored == code if stored else False
