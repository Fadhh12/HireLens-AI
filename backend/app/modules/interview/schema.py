"""Pydantic schemas for interview guides (FR-8)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterviewGuideUpdate(BaseModel):
    """FR-8.2: interviewer edits before finalizing."""

    technical_questions: list[str] | None = None
    behavioral_questions: list[str] | None = None
    risk_areas: list[str] | None = None


class InterviewGuideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    technical_questions: list[str]
    behavioral_questions: list[str]
    risk_areas: list[str]
    version: int
    is_final: bool
    created_by: uuid.UUID
    created_at: datetime
