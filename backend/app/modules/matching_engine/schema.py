"""Pydantic schema for candidate score responses (SDD §4 example response)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.matching_engine.model import MatchLabel


class CandidateScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    skill_fit_score: float
    experience_fit_score: float
    values_fit_score: float | None
    final_score: float
    label: MatchLabel
    score_breakdown: dict
    model_version: str
    computed_at: datetime
