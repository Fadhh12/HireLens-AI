"""SQLAlchemy model for `interview_guides` (SDD §3.1, FR-8)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_json_list = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InterviewGuide(Base):
    __tablename__ = "interview_guides"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("candidates.id"), nullable=False, index=True
    )

    technical_questions: Mapped[list[str]] = mapped_column(_json_list, nullable=False, default=list)
    behavioral_questions: Mapped[list[str]] = mapped_column(_json_list, nullable=False, default=list)
    risk_areas: Mapped[list[str]] = mapped_column(_json_list, nullable=False, default=list)

    # FR-8.3: regenerating creates a new row, never overwrites — version
    # numbers the history per candidate.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Not in SDD §3.1's column list, but FR-8.2 talks about a "final
    # interview guide" and UI/UX Layar 9 has a "Finalisasi Guide" button
    # that locks it — same pattern as other Phase gaps, added here.
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
