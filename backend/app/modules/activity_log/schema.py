"""Pydantic schema for activity log entries (UI/UX Layar 10)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID | None
    actor_id: uuid.UUID
    actor_name: str
    action: str
    old_value: str | None
    new_value: str | None
    created_at: datetime
