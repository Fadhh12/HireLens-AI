"""
FastAPI dependencies: current-user extraction from a JWT bearer token,
plus role guards enforcing the SRS §2 role matrix
(admin / recruiter / hiring_manager / interviewer).
"""

import secrets
from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.session import get_db
from app.modules.auth.model import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = db.get(User, UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise unauthorized

    # A logout (or role change) bumps token_version — any access token minted
    # before that no longer matches, so it's rejected even before it expires.
    if user.token_version != payload.get("token_version"):
        raise unauthorized

    return user


def require_role(*roles: str) -> Callable[[User], User]:
    """Usage: Depends(require_role("admin")) or Depends(require_role("admin", "recruiter"))."""

    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak punya akses untuk aksi ini",
            )
        return current_user

    return _guard


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Guards the public intake bridge (Google Form -> Apps Script -> this
    API) — the caller there is a script holding a shared secret, not a user
    with a JWT, so this is a separate, deliberately narrow auth path (only
    the one endpoint uses it). Not configuring PUBLIC_APPLY_API_KEY disables
    the endpoint entirely (503) rather than defaulting it open."""
    configured = get_settings().public_apply_api_key
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Public intake belum dikonfigurasi (PUBLIC_APPLY_API_KEY kosong)",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, configured):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key tidak valid")
