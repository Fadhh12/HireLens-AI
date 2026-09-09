"""Auth endpoints: POST /login, /refresh, /logout (FR-1.1-1.4). Phase 1."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# TODO(Phase 1): POST /login  -> access + refresh token
# TODO(Phase 1): POST /refresh -> new access token
# TODO(Phase 1): POST /logout  -> invalidate refresh token
