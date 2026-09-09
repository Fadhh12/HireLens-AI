"""Auth endpoints (FR-1.1-1.4) + admin-only user management (FR-1.5, UI/UX Layar 11)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.model import User
from app.modules.auth.schema import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


def _tokens_for(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value, user.token_version),
        refresh_token=create_refresh_token(user.id, user.role.value, user.token_version),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = service.authenticate_user(db, payload.email, payload.password)
    return _tokens_for(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token tidak valid atau sudah kedaluwarsa",
    )
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = db.get(User, uuid.UUID(decoded["sub"]))
    if user is None or not user.is_active or user.token_version != decoded.get("token_version"):
        raise unauthorized

    # Rotate both tokens so a leaked refresh token can't be replayed indefinitely.
    return _tokens_for(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    service.logout(db, current_user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


# --- User management (Admin-only) ---


@users_router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> list[User]:
    return service.list_users(db)


@users_router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> User:
    return service.create_user(db, payload)


@users_router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> User:
    return service.get_user(db, user_id)


@users_router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> User:
    return service.update_user(db, user_id, payload)
