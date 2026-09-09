"""Interview guide endpoints: generate/get/edit/finalize (FR-8, BR-4)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.interview import service
from app.modules.interview.model import InterviewGuide
from app.modules.interview.schema import InterviewGuideOut, InterviewGuideUpdate
from app.workers.tasks_interview import generate_interview_guide_task

router = APIRouter(tags=["interview"])


@router.post("/candidates/{candidate_id}/interview-guide", status_code=202)
def trigger_generate_guide(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "interviewer")),
) -> dict:
    service.check_eligible_for_guide(db, candidate_id)  # BR-4, synchronous so callers get real feedback
    generate_interview_guide_task.delay(str(candidate_id), str(current_user.id))
    return {"detail": "Interview guide sedang di-generate"}


@router.get("/candidates/{candidate_id}/interview-guide", response_model=InterviewGuideOut)
def get_latest_guide(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> InterviewGuide:
    return service.get_latest_guide(db, candidate_id)


@router.get("/candidates/{candidate_id}/interview-guide/versions", response_model=list[InterviewGuideOut])
def list_guide_versions(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[InterviewGuide]:
    return service.list_guide_versions(db, candidate_id)


@router.patch("/interview-guide/{guide_id}", response_model=InterviewGuideOut)
def update_guide(
    guide_id: uuid.UUID,
    payload: InterviewGuideUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "interviewer")),
) -> InterviewGuide:
    return service.update_guide(db, guide_id, payload)


@router.post("/interview-guide/{guide_id}/finalize", response_model=InterviewGuideOut)
def finalize_guide(
    guide_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "interviewer")),
) -> InterviewGuide:
    return service.finalize_guide(db, guide_id)
