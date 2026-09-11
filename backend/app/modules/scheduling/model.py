"""SQLAlchemy models for Google Calendar interview scheduling.

New module, not part of the original SDD/SRS — added per a later
feature request: once a candidate is shortlisted, HR schedules an
interview and a Google Meet link + calendar invite go out to the
candidate automatically (FR-8/BR-4's "interview" concept previously
only covered the AI-generated question guide in interview/model.py,
never an actual calendar event).

Two tables:
- `google_credentials`: one row per recruiter who has connected their
  own Google account. Deliberately per-recruiter OAuth, not one shared
  service account — that would need Google Workspace admin access
  (domain-wide delegation) this project doesn't assume the user has.
- `interview_schedules`: one row per scheduled interview, linking a
  candidate to the Calendar event + Meet link that was created for it.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GoogleCredential(Base):
    """1:1 with `users.id` — a recruiter connects at most one Google account.

    `refresh_token` is what avoids re-connecting every session; Google
    only issues one on the *first* consent for a given app+user, so the
    OAuth flow (google_client.py) always requests
    access_type=offline + prompt=consent to guarantee getting one even
    on a re-connect.
    """

    __tablename__ = "google_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), primary_key=True)
    google_email: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Cached short-lived access token, so most requests skip a refresh
    # round-trip — google_client.py refreshes it once access_token_expires_at
    # has passed and rewrites both columns.
    access_token: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class InterviewSchedule(Base):
    __tablename__ = "interview_schedules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("candidates.id"), nullable=False, index=True)
    scheduled_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    google_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    meet_link: Mapped[str] = mapped_column(String(500), nullable=False)
    # Link to the event in the recruiter's own Google Calendar UI — handy in
    # the response so the frontend can offer "buka di Google Calendar".
    calendar_html_link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
