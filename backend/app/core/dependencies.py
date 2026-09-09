"""
FastAPI dependencies: current-user extraction from JWT + role guards.

Implemented in Phase 1 (auth) — routers in later phases import
`require_role(...)` from here to enforce SRS §2's role matrix
(admin / recruiter / hiring_manager / interviewer).
"""

# TODO(Phase 1): get_current_user(token: str = Depends(oauth2_scheme)) -> User
# TODO(Phase 1): require_role(*roles: str) -> Callable dependency
