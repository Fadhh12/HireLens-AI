"""Auth + user management business logic.

FR-1.4 lockout: 5 consecutive failed attempts locks the account for 15
minutes. Counter lives on the user row (see model.py docstring).
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.modules.auth.model import User
from app.modules.auth.schema import UserCreate, UserUpdate

settings = get_settings()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime) -> datetime:
    """SQLite (used in tests) drops tzinfo on round-trip even for
    DateTime(timezone=True) columns; Postgres doesn't. Normalize so the
    comparison below works the same on both."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def authenticate_user(db: Session, email: str, password: str) -> User:
    """FR-1.1 + FR-1.4. Raises HTTPException(401) on bad credentials, or
    HTTPException(423 Locked) while the lockout window is active."""
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email atau kata sandi salah",
    )

    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        raise generic_error

    if user.locked_until is not None and _as_aware(user.locked_until) > _now():
        remaining_minutes = max(1, int((_as_aware(user.locked_until) - _now()).total_seconds() // 60) + 1)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Akun dikunci sementara, coba lagi dalam {remaining_minutes} menit",
        )

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.login_max_attempts:
            user.locked_until = _now() + timedelta(minutes=settings.login_lockout_minutes)
            user.failed_login_attempts = 0
        db.commit()
        raise generic_error

    # Successful login resets the counter.
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)
    return user


def logout(db: Session, user: User) -> None:
    """Bumps token_version so every access/refresh token issued before this
    point stops verifying (see core/dependencies.get_current_user)."""
    user.token_version += 1
    db.commit()


def create_user(db: Session, data: UserCreate) -> User:
    """Admin-only (FR-1.5: role is always set by Admin, no self-registration)."""
    if get_user_by_email(db, data.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )
    user = User(
        id=uuid.uuid4(),
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
    return user


def update_user(db: Session, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = get_user(db, user_id)
    if data.name is not None:
        user.name = data.name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
        if not data.is_active:
            # Deactivating an account also invalidates any tokens it's holding.
            user.token_version += 1
    db.commit()
    db.refresh(user)
    return user
