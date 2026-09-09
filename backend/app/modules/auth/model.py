"""
SQLAlchemy model for `users` (SDD §3.1).

Placed under modules/auth (not a separate `users` module) — SDD §5's
folder listing gives `auth/` a router/schema/service but no model.py,
which left the model's home ambiguous. `users` naturally belongs to
the auth domain (SDD's own architecture diagram groups "Job, User,
Candidate CRUD, Auth" as one Core Service), so it lives here rather
than inventing a new top-level module.

Two deviations from the exact SDD §3.1 column list, both required by
FRs the schema didn't otherwise have storage for:
- `failed_login_attempts` / `locked_until` — FR-1.4's 5-strikes lockout
  needs somewhere to live; kept on the row instead of a new table since
  it's simple per-user counter state.
- `is_active` — UI/UX Layar 11 (User Management) calls for an admin
  "nonaktifkan akun" action.
- `token_version` — bumped on logout so previously issued refresh
  tokens stop verifying (see app/core/security.py); simplest way to
  get FR-1.3/SDD's POST /auth/logout "invalidate refresh token"
  without a server-side token blocklist table.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    recruiter = "recruiter"
    hiring_manager = "hiring_manager"
    interviewer = "interviewer"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
