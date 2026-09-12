"""Google account connection + interview scheduling.

Flow: a recruiter connects their own Google account once (OAuth,
per-user — see google_client.py's docstring on why not a shared
service account). After that, scheduling an interview for a
shortlisted+ candidate creates a Calendar event with a Google Meet
link under that recruiter's calendar, adds the candidate as an
attendee (without Calendar's own auto-invite email — see
google_client.create_interview_event's send_updates default), and
sends the candidate a templated Gmail invite with the Meet link
(messaging/service.py's "interview" trigger) instead."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.activity_log.service import log_activity
from app.modules.candidates.model import CandidateStatus
from app.modules.candidates.service import get_candidate
from app.modules.jobs.service import get_job
from app.modules.scheduling import google_client
from app.modules.scheduling.google_client import GoogleCalendarError
from app.modules.scheduling.model import GoogleCredential, InterviewSchedule
from app.modules.scheduling.schema import InterviewScheduleCreate

# Scheduling only makes sense once a candidate has passed screening and
# before the pipeline is closed out — mirrors the "kandidat yang lolos
# screening" framing of the feature request more narrowly than
# interview/service.py's guide-eligibility set (which also allows
# hired/rejected, since a guide is historical record; a *new* interview
# invite for an already-hired/rejected candidate wouldn't make sense).
_SCHEDULABLE_STATUSES = {CandidateStatus.shortlisted, CandidateStatus.interviewed}

_STATE_TOKEN_TYPE = "google_oauth_state"  # noqa: S105 - not a secret, just a discriminator claim


def _sign_state(user_id: uuid.UUID, return_to: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": _STATE_TOKEN_TYPE,
        "return_to": return_to,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _verify_state(state: str) -> tuple[uuid.UUID, str]:
    settings = get_settings()
    try:
        payload = jwt.decode(state, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State OAuth tidak valid/kedaluwarsa") from exc
    if payload.get("type") != _STATE_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="State OAuth tidak valid")
    return uuid.UUID(payload["sub"]), payload.get("return_to") or "/dashboard/candidates"


def get_connect_url(user_id: uuid.UUID, return_to: str) -> str:
    try:
        return google_client.build_authorization_url(state=_sign_state(user_id, return_to))
    except GoogleCalendarError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def handle_callback(db: Session, code: str, state: str) -> tuple[uuid.UUID, str]:
    """Returns (user id, return_to path) so the router can redirect back to
    wherever the recruiter started connecting from."""
    user_id, return_to = _verify_state(state)
    try:
        tokens = google_client.exchange_code(code)
    except GoogleCalendarError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    existing = db.get(GoogleCredential, user_id)
    if existing:
        existing.google_email = tokens.google_email or existing.google_email
        existing.refresh_token = tokens.refresh_token
        existing.access_token = tokens.access_token
        existing.access_token_expires_at = tokens.expires_at
    else:
        db.add(
            GoogleCredential(
                user_id=user_id,
                google_email=tokens.google_email,
                refresh_token=tokens.refresh_token,
                access_token=tokens.access_token,
                access_token_expires_at=tokens.expires_at,
            )
        )
    db.commit()
    return user_id, return_to


def get_connection_status(db: Session, user_id: uuid.UUID) -> GoogleCredential | None:
    return db.get(GoogleCredential, user_id)


def disconnect(db: Session, user_id: uuid.UUID) -> None:
    cred = db.get(GoogleCredential, user_id)
    if cred:
        db.delete(cred)
        db.commit()


def schedule_interview(
    db: Session,
    candidate_id: uuid.UUID,
    data: InterviewScheduleCreate,
    actor_id: uuid.UUID,
) -> InterviewSchedule:
    candidate = get_candidate(db, candidate_id)
    if candidate.status not in _SCHEDULABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview hanya bisa dijadwalkan untuk kandidat berstatus shortlisted/interviewed",
        )
    if not candidate.email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Kandidat tidak punya alamat email")

    credential = db.get(GoogleCredential, actor_id)
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hubungkan Google Calendar Anda dulu sebelum menjadwalkan interview",
        )

    job = get_job(db, candidate.job_posting_id)
    start, end = google_client.default_interview_window(data.scheduled_at, data.duration_minutes)

    try:
        created = google_client.create_interview_event(
            refresh_token=credential.refresh_token,
            summary=f"Interview {candidate.full_name} — {job.title}",
            description=(
                f"Interview kandidat {candidate.full_name} untuk posisi {job.title}.\n"
                "Dijadwalkan otomatis lewat HireLens AI."
            ),
            start=start,
            end=end,
            attendee_emails=[candidate.email],
        )
    except GoogleCalendarError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    schedule = InterviewSchedule(
        id=uuid.uuid4(),
        candidate_id=candidate_id,
        scheduled_by=actor_id,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        google_event_id=created.event_id,
        meet_link=created.meet_link,
        calendar_html_link=created.html_link,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    log_activity(
        db,
        actor_id=actor_id,
        action="interview_scheduled",
        candidate_id=candidate_id,
        new_value=data.scheduled_at.isoformat(),
    )

    # Local import — avoids a module-load-order cycle (messaging imports
    # scheduling.google_client/model). Best-effort: the interview is
    # already on the calendar either way; a failed notification email
    # shouldn't undo that.
    from app.modules.messaging.service import send_interview_email

    send_interview_email(
        db,
        candidate,
        actor_id=actor_id,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        meet_link=schedule.meet_link,
    )
    return schedule


def list_schedules(db: Session, candidate_id: uuid.UUID) -> list[InterviewSchedule]:
    return list(
        db.query(InterviewSchedule)
        .filter(InterviewSchedule.candidate_id == candidate_id)
        .order_by(InterviewSchedule.scheduled_at.desc())
        .all()
    )
