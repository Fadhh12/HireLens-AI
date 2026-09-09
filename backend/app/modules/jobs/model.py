"""SQLAlchemy model for `job_postings` (SDD §3.1)."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobLevel(str, enum.Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"


class JobStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    closed = "closed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Generic JSON, swapped for native JSONB on Postgres — SQLite (used in
# tests) can't compile the Postgres-specific type.
_json_list = JSON().with_variant(JSONB(), "postgresql")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    required_skills: Mapped[list[str]] = mapped_column(_json_list, nullable=False, default=list)
    nice_to_have_skills: Mapped[list[str]] = mapped_column(_json_list, nullable=False, default=list)

    min_experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[JobLevel] = mapped_column(Enum(JobLevel, name="job_level"), nullable=False)

    weight_skill_fit: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=50)
    weight_experience_fit: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=30)
    weight_values_fit: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=20)

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.draft
    )

    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
