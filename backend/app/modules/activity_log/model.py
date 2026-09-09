"""SQLAlchemy model for `activity_logs` (SDD §3.1, FR-7.3).

Not one of SDD §5's listed folders (no module owns it explicitly) —
given its own module since it's genuinely cross-cutting (candidates,
jobs, scoring could all log into it) and UI/UX Layar 10 treats it as
a first-class screen, unlike the auth/matching_engine model.py gaps
which clearly belonged to an existing module.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("candidates.id"), nullable=True, index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
