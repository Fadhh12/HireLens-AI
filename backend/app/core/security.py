"""
Password hashing + JWT issuing/verification (FR-1.2, FR-1.3).

Uses `bcrypt` directly rather than passlib — passlib 1.7.4 is
unmaintained and crashes against bcrypt>=4.1 (see requirements.txt).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings

settings = get_settings()

TokenType = Literal["access", "refresh"]


# --- Password hashing (FR-1.2) ---


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


# --- JWT (FR-1.3: access 15-60 min, refresh 7 days) ---


def _create_token(user_id: uuid.UUID, role: str, token_version: int, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "token_version": token_version,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID, role: str, token_version: int) -> str:
    return _create_token(
        user_id, role, token_version, "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: uuid.UUID, role: str, token_version: int) -> str:
    return _create_token(
        user_id, role, token_version, "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> dict:
    """Decode + validate a JWT. Raises jwt.InvalidTokenError (incl. ExpiredSignatureError)
    on any problem — callers turn that into a 401."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token, got {payload.get('type')}")
    return payload
