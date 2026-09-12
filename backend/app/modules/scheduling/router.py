"""Google Calendar connect/status/disconnect + interview scheduling
endpoints. Not part of the original SDD — see scheduling/model.py."""

import uuid
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.scheduling import service
from app.modules.scheduling.model import InterviewSchedule
from app.modules.scheduling.schema import (
    GoogleConnectionStatus,
    InterviewScheduleCreate,
    InterviewScheduleOut,
    UpcomingInterviewOut,
)

router = APIRouter(tags=["scheduling"])

# Scheduling an interview / connecting a calendar is an HR action — same
# role set as candidate status changes (FR-7.2), since the two go together
# in the intended flow (shortlist -> schedule interview).
_SCHEDULING_ROLES = ("admin", "recruiter", "hiring_manager")


@router.get("/integrations/google/connect")
def connect_google(
    return_to: str = Query(default="/dashboard/candidates"),
    current_user: User = Depends(require_role(*_SCHEDULING_ROLES)),
) -> dict:
    """Returns the Google consent URL for the frontend to redirect to —
    not a redirect itself, since this call needs the caller's bearer
    token (to know whose account is connecting), which a top-level
    browser navigation can't send."""
    url = service.get_connect_url(current_user.id, return_to)
    return {"authorize_url": url}


@router.get("/integrations/google/callback")
def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Google redirects the browser here after consent — no Authorization
    header available, the JWT `state` param is the only trusted context."""
    frontend_url = get_settings().frontend_url.rstrip("/")

    if error or not code or not state:
        return RedirectResponse(f"{frontend_url}/dashboard/candidates?google_error={urllib.parse.quote(error or 'batal')}")

    try:
        _, return_to = service.handle_callback(db, code, state)
    except HTTPException as exc:
        return RedirectResponse(f"{frontend_url}/dashboard/candidates?google_error={urllib.parse.quote(str(exc.detail))}")

    separator = "&" if "?" in return_to else "?"
    return RedirectResponse(f"{frontend_url}{return_to}{separator}google_connected=1")


@router.get("/integrations/google/status", response_model=GoogleConnectionStatus)
def google_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoogleConnectionStatus:
    cred = service.get_connection_status(db, current_user.id)
    if cred is None:
        return GoogleConnectionStatus(connected=False)
    return GoogleConnectionStatus(connected=True, google_email=cred.google_email)


@router.delete("/integrations/google", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_google(
    current_user: User = Depends(require_role(*_SCHEDULING_ROLES)),
    db: Session = Depends(get_db),
) -> None:
    service.disconnect(db, current_user.id)


@router.post(
    "/candidates/{candidate_id}/interview-schedule",
    response_model=InterviewScheduleOut,
    status_code=201,
)
def create_interview_schedule(
    candidate_id: uuid.UUID,
    payload: InterviewScheduleCreate,
    current_user: User = Depends(require_role(*_SCHEDULING_ROLES)),
    db: Session = Depends(get_db),
) -> InterviewSchedule:
    return service.schedule_interview(db, candidate_id, payload, actor_id=current_user.id)


@router.get(
    "/candidates/{candidate_id}/interview-schedule",
    response_model=list[InterviewScheduleOut],
)
def list_interview_schedules(
    candidate_id: uuid.UUID,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InterviewSchedule]:
    return service.list_schedules(db, candidate_id)


@router.get("/interview-schedules/upcoming", response_model=list[UpcomingInterviewOut])
def list_upcoming_interviews(
    limit: int = Query(default=5, ge=1, le=20),
    _: User = Depends(require_role("admin", "recruiter", "hiring_manager")),
    db: Session = Depends(get_db),
) -> list[UpcomingInterviewOut]:
    """Dashboard overview widget — same role scope as the Job Aktif
    section it sits next to."""
    return service.list_upcoming_interviews(db, limit)
