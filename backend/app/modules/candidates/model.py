"""SQLAlchemy model for `candidates` (SDD §3.1)."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidateStatus(str, enum.Enum):
    new = "new"
    screening = "screening"
    shortlisted = "shortlisted"
    interviewed = "interviewed"
    hired = "hired"
    rejected = "rejected"
    needs_manual_review = "needs_manual_review"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_json_dict = JSON().with_variant(JSONB(), "postgresql")
_json_list = JSON().with_variant(JSONB(), "postgresql")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("job_postings.id"), nullable=False, index=True
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    cv_file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    certificate_urls: Mapped[list[str]] = mapped_column(_json_list, nullable=False, default=list)

    # Structured extraction result (FR-4.2) — see document_ai/parser.py for
    # the shape: each field carries {"value": ..., "verified": bool} so the
    # UI can show FR-4.4's confidence indicator. Null until parsing runs.
    parsed_profile: Mapped[dict | None] = mapped_column(_json_dict, nullable=True)

    # Manual assessment input (FR-3.3) — e.g. {"mbti": "INTJ", "competency_scores": {...}}
    assessment_input: Mapped[dict | None] = mapped_column(_json_dict, nullable=True)

    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, name="candidate_status"), nullable=False, default=CandidateStatus.new
    )
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
