"""Interview guide orchestration + versioning (FR-8, BR-4)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.candidates.model import CandidateStatus
from app.modules.candidates.service import get_candidate
from app.modules.interview.model import InterviewGuide
from app.modules.interview.question_generator import QuestionGenerationError, generate_interview_guide
from app.modules.interview.schema import InterviewGuideUpdate
from app.modules.jobs.service import get_job
from app.modules.matching_engine.service import get_latest_score

# BR-4: "kandidat berstatus shortlisted atau setelahnya".
_ALLOWED_STATUSES = {
    CandidateStatus.shortlisted,
    CandidateStatus.interviewed,
    CandidateStatus.hired,
    CandidateStatus.rejected,
}


def check_eligible_for_guide(db: Session, candidate_id: uuid.UUID) -> None:
    """BR-4, checked synchronously by the router before enqueueing the
    Celery task — otherwise the request always returns 202 (task
    accepted) and an ineligible candidate silently never gets a guide,
    with no feedback to the caller. The task itself re-checks too, since
    status could change between the request and the task running."""
    candidate = get_candidate(db, candidate_id)
    if candidate.status not in _ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview guide hanya bisa di-generate untuk kandidat berstatus shortlisted atau setelahnya (BR-4)",
        )


def generate_guide(db: Session, candidate_id: uuid.UUID, actor_id: uuid.UUID) -> InterviewGuide:
    candidate = get_candidate(db, candidate_id)
    if candidate.status not in _ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview guide hanya bisa di-generate untuk kandidat berstatus shortlisted atau setelahnya (BR-4)",
        )
    job = get_job(db, candidate.job_posting_id)

    score_breakdown = None
    try:
        score_breakdown = get_latest_score(db, candidate_id).score_breakdown
    except HTTPException:
        pass  # no score yet — generator still works, just without the gap context

    try:
        result = generate_interview_guide(candidate, job, score_breakdown)
    except QuestionGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    latest_version = db.scalar(
        select(InterviewGuide.version)
        .where(InterviewGuide.candidate_id == candidate_id)
        .order_by(InterviewGuide.version.desc())
        .limit(1)
    )
    next_version = (latest_version or 0) + 1

    guide = InterviewGuide(
        id=uuid.uuid4(),
        candidate_id=candidate_id,
        technical_questions=result["technical_questions"],
        behavioral_questions=result["behavioral_questions"],
        risk_areas=result["risk_areas"],
        version=next_version,
        created_by=actor_id,
    )
    db.add(guide)
    db.commit()
    db.refresh(guide)
    return guide


def get_latest_guide(db: Session, candidate_id: uuid.UUID) -> InterviewGuide:
    guide = db.scalar(
        select(InterviewGuide)
        .where(InterviewGuide.candidate_id == candidate_id)
        .order_by(InterviewGuide.version.desc())
        .limit(1)
    )
    if guide is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belum ada interview guide untuk kandidat ini",
        )
    return guide


def list_guide_versions(db: Session, candidate_id: uuid.UUID) -> list[InterviewGuide]:
    return list(
        db.scalars(
            select(InterviewGuide)
            .where(InterviewGuide.candidate_id == candidate_id)
            .order_by(InterviewGuide.version.desc())
        )
    )


def get_guide(db: Session, guide_id: uuid.UUID) -> InterviewGuide:
    guide = db.get(InterviewGuide, guide_id)
    if guide is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview guide tidak ditemukan")
    return guide


def update_guide(db: Session, guide_id: uuid.UUID, data: InterviewGuideUpdate) -> InterviewGuide:
    guide = get_guide(db, guide_id)
    if guide.is_final:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview guide yang sudah difinalisasi tidak bisa diedit",
        )
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(guide, field, value)
    db.commit()
    db.refresh(guide)
    return guide


def finalize_guide(db: Session, guide_id: uuid.UUID) -> InterviewGuide:
    guide = get_guide(db, guide_id)
    guide.is_final = True
    db.commit()
    db.refresh(guide)
    return guide
