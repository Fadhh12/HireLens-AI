"""Pydantic schemas for Google Calendar interview scheduling."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GoogleConnectionStatus(BaseModel):
    connected: bool
    google_email: str | None = None


class InterviewScheduleCreate(BaseModel):
    # ISO 8601 with timezone offset — the frontend's <input type="datetime-local">
    # is naive, so it attaches the browser's own offset before sending.
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=240)


class InterviewScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    scheduled_by: uuid.UUID
    scheduled_at: datetime
    duration_minutes: int
    meet_link: str
    calendar_html_link: str | None


class UpcomingInterviewOut(BaseModel):
    """Dashboard overview widget — InterviewSchedule joined with the
    candidate/job names it doesn't itself carry (denormalized read model,
    same reasoning as CandidateListItemOut)."""

    id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_photo_url: str | None
    job_title: str
    scheduled_at: datetime
    duration_minutes: int
    meet_link: str
    created_at: datetime
