"""Pydantic schemas for status-change email templates + sent/reply log."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.messaging.model import EmailTrigger


class EmailTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger: EmailTrigger
    subject: str
    body: str
    updated_at: datetime


class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str


class CandidateEmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    sent_by: uuid.UUID
    trigger: EmailTrigger
    subject: str
    body: str
    attachment_filename: str | None
    has_reply: bool
    reply_snippet: str | None
    reply_detected_at: datetime | None
    sent_at: datetime
