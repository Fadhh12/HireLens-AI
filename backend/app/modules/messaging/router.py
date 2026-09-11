"""Email template management + status-change email sending/reply log.
Not part of the original SDD — see messaging/model.py."""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.candidates.service import get_candidate
from app.modules.messaging import service
from app.modules.messaging.model import CandidateEmail, EmailTemplate, EmailTrigger
from app.modules.messaging.schema import CandidateEmailOut, EmailTemplateOut, EmailTemplateUpdate

router = APIRouter(tags=["messaging"])

# Template management is HR configuration — same scope as job scoring
# weights (admin/recruiter). Sending/viewing widens to hiring_manager
# too, matching candidate status-change permissions (FR-7.2).
_TEMPLATE_ROLES = ("admin", "recruiter")
_SEND_ROLES = ("admin", "recruiter", "hiring_manager")

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MB — same ballpark as CV uploads


@router.get("/email-templates", response_model=list[EmailTemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(*_TEMPLATE_ROLES)),
) -> list[EmailTemplate]:
    return service.list_templates(db)


@router.patch("/email-templates/{trigger}", response_model=EmailTemplateOut)
def update_template(
    trigger: EmailTrigger,
    payload: EmailTemplateUpdate,
    current_user: User = Depends(require_role(*_TEMPLATE_ROLES)),
    db: Session = Depends(get_db),
) -> EmailTemplate:
    return service.update_template(db, trigger, payload, actor_id=current_user.id)


@router.post("/email-templates/poll-replies")
def poll_replies_now(
    _: User = Depends(require_role(*_TEMPLATE_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    """Manual fallback for the background poll loop (app/main.py) — use
    this if replies aren't showing up (e.g. the host process doesn't stay
    warm long enough for the periodic loop to matter)."""
    found = service.poll_replies(db)
    return {"new_replies": found}


@router.post(
    "/candidates/{candidate_id}/send-email",
    response_model=CandidateEmailOut,
    status_code=201,
)
async def send_status_email(
    candidate_id: uuid.UUID,
    trigger: EmailTrigger = Form(...),
    attachment: UploadFile | None = File(default=None),
    current_user: User = Depends(require_role(*_SEND_ROLES)),
    db: Session = Depends(get_db),
) -> CandidateEmail:
    """Explicit send — used to (re)send with an attachment (assessment
    PDF for shortlisted, contract for hired) since the automatic email
    fired on the status change itself never carries one."""
    candidate = get_candidate(db, candidate_id)

    attachment_tuple = None
    if attachment is not None:
        content = await attachment.read()
        if len(content) > MAX_ATTACHMENT_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Lampiran maksimal 10MB")
        attachment_tuple = (attachment.filename or "lampiran.pdf", attachment.content_type or "application/pdf", content)

    return service.send_status_email(db, candidate, trigger, actor_id=current_user.id, attachment=attachment_tuple)


@router.get("/candidates/{candidate_id}/emails", response_model=list[CandidateEmailOut])
def list_candidate_emails(
    candidate_id: uuid.UUID,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CandidateEmail]:
    return service.list_candidate_emails(db, candidate_id)
