"""SQLAlchemy models for status-change email templates + the sent/reply log.

New module, not part of the original SDD/SRS — added per a feature
request: when a candidate is moved to shortlisted/rejected/hired, send
a templated email automatically (Gmail, via the same per-recruiter
Google connection as scheduling/), and let HR know if the candidate
replies.

Two tables:
- `email_templates`: one editable row per trigger status (shortlisted/
  rejected/hired — interview is deliberately excluded, that's still the
  Calendar invite from scheduling/). Global, not per-job — placeholders
  ({{full_name}}, {{job_title}}, {{department}}) cover the "sesuaikan
  isi per bidang yang dilamar" part instead of one template per job.
- `candidate_emails`: one row per email actually sent, holding the
  Gmail thread/message id so poll_replies (service.py) can check that
  thread later for a candidate reply.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmailTrigger(str, enum.Enum):
    shortlisted = "shortlisted"
    rejected = "rejected"
    hired = "hired"
    # Sent by scheduling/service.py's schedule_interview, not
    # candidates/service.py's update_status like the other three —
    # scheduling an interview isn't itself a candidate status transition.
    interview = "interview"


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    trigger: Mapped[EmailTrigger] = mapped_column(Enum(EmailTrigger, name="email_trigger"), primary_key=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class CandidateEmail(Base):
    __tablename__ = "candidate_emails"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("candidates.id"), nullable=False, index=True)
    sent_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    trigger: Mapped[EmailTrigger] = mapped_column(Enum(EmailTrigger, name="email_trigger"), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    gmail_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    gmail_message_id: Mapped[str] = mapped_column(String(255), nullable=False)

    has_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reply_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
