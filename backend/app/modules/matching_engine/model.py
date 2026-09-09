"""SQLAlchemy model for `candidate_scores` (SDD §3.1).

Placed under modules/matching_engine (not listed as its own model.py in
SDD §5's folder listing, same gap as modules/auth — see auth/model.py's
docstring for the precedent) since the table is that domain's data.

One candidate has MANY score rows (SDD §3.2: "histori tiap kali
dihitung ulang") — recomputing never overwrites, it inserts a new row.
"Current" score is just the most recent by computed_at.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MatchLabel(str, enum.Enum):
    strong_match = "strong_match"
    consider = "consider"
    not_a_fit = "not_a_fit"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_json_dict = JSON().with_variant(JSONB(), "postgresql")


class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("candidates.id"), nullable=False, index=True
    )

    skill_fit_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    experience_fit_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    values_fit_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    final_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    label: Mapped[MatchLabel] = mapped_column(Enum(MatchLabel, name="match_label"), nullable=False)

    # FR-5.3 explainability + BR-5 audit trail: the full breakdown (per-
    # component scores/weights/matched-missing skills/candidate summary/
    # values-fit note) plus a snapshot of the inputs used, so this row is
    # self-contained even if the candidate/job record changes later.
    score_breakdown: Mapped[dict] = mapped_column(_json_dict, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
