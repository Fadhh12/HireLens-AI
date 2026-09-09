"""Unit tests for FR-1.1/1.4/1.5 auth business logic (app/modules/auth/service.py)."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.auth import service
from app.modules.auth.model import UserRole
from app.modules.auth.schema import UserCreate


@pytest.fixture()
def admin_user(db_session: Session):
    return service.create_user(
        db_session,
        UserCreate(name="Admin", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.admin),
    )


def test_authenticate_success(db_session: Session, admin_user) -> None:
    user = service.authenticate_user(db_session, "admin@hirelens.ai", "Passw0rd")
    assert user.id == admin_user.id
    assert user.failed_login_attempts == 0


def test_authenticate_wrong_password_increments_counter(db_session: Session, admin_user) -> None:
    with pytest.raises(HTTPException) as exc:
        service.authenticate_user(db_session, "admin@hirelens.ai", "wrong-password")
    assert exc.value.status_code == 401

    db_session.refresh(admin_user)
    assert admin_user.failed_login_attempts == 1


def test_authenticate_locks_after_max_attempts(db_session: Session, admin_user) -> None:
    """FR-1.4: 5 consecutive failures locks the account for 15 minutes."""
    for _ in range(5):
        with pytest.raises(HTTPException):
            service.authenticate_user(db_session, "admin@hirelens.ai", "wrong-password")

    # 6th attempt, even with the CORRECT password, must be rejected as locked.
    with pytest.raises(HTTPException) as exc:
        service.authenticate_user(db_session, "admin@hirelens.ai", "Passw0rd")
    assert exc.value.status_code == 423

    db_session.refresh(admin_user)
    assert admin_user.locked_until is not None
    assert admin_user.failed_login_attempts == 0  # reset when the lock kicks in


def test_authenticate_unknown_email_is_generic_error(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc:
        service.authenticate_user(db_session, "nobody@hirelens.ai", "whatever1")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Email atau kata sandi salah"


def test_create_user_duplicate_email_rejected(db_session: Session, admin_user) -> None:
    with pytest.raises(HTTPException) as exc:
        service.create_user(
            db_session,
            UserCreate(name="Dup", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.recruiter),
        )
    assert exc.value.status_code == 409


def test_logout_bumps_token_version(db_session: Session, admin_user) -> None:
    assert admin_user.token_version == 0
    service.logout(db_session, admin_user)
    assert admin_user.token_version == 1
