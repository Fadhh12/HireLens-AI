"""Pydantic request/response schemas for auth + user management
(FR-1, SRS §4 validation rules, UI/UX Layar 11)."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.modules.auth.model import UserRole

_PASSWORD_MIN_LENGTH = 8


def _validate_password_strength(password: str) -> str:
    """SRS §4: minimal 8 karakter, kombinasi huruf & angka."""
    if len(password) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password minimal {_PASSWORD_MIN_LENGTH} karakter")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password harus mengandung minimal 1 huruf")
    if not re.search(r"\d", password):
        raise ValueError("Password harus mengandung minimal 1 angka")
    return password


# --- Auth ---


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- User management (Admin-only, FR-1.5 / UI/UX Layar 11) ---


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserUpdate(BaseModel):
    name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
