"""Candidate intake/list/detail endpoints (FR-3, FR-6 partial, FR-4.3)."""

import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.candidates import service
from app.modules.candidates.model import Candidate
from app.modules.candidates.schema import (
    CandidateCreateResponse,
    CandidateIntakeForm,
    CandidateListItemOut,
    CandidateOut,
    CandidateStatusUpdate,
    CandidateUpdate,
)
from app.modules.jobs.model import JobStatus
from app.modules.jobs.service import get_job
from app.modules.matching_engine import service as matching_service
from app.modules.matching_engine.schema import CandidateScoreOut
from app.workers.tasks_parsing import parse_candidate_documents
from app.workers.tasks_scoring import compute_candidate_score
from sqlalchemy.orm import Session

router = APIRouter(tags=["candidates"])


@router.post(
    "/jobs/{job_id}/candidates",
    response_model=CandidateCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def intake_candidate(
    job_id: uuid.UUID,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    assessment_input: str | None = Form(default=None),
    cv_file: UploadFile = File(...),
    certificate_files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> CandidateCreateResponse:
    job = get_job(db, job_id)
    if job.status == JobStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job posting ini sudah closed, tidak menerima kandidat baru (FR-2.4)",
        )

    try:
        form = CandidateIntakeForm(full_name=full_name, email=email, phone=phone)
    except ValidationError as exc:
        # Manual instantiation (not FastAPI's own Form/body parsing), so its
        # ValidationError needs converting to a 422 by hand — otherwise it
        # escapes as an unhandled 500. Pydantic's raw .errors() embeds the
        # original exception object in each entry's "ctx", which isn't JSON
        # serializable, so pull out just the plain messages.
        messages = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=messages) from exc

    parsed_assessment: dict | None = None
    if assessment_input:
        try:
            parsed_assessment = json.loads(assessment_input)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="assessment_input harus berupa JSON valid",
            ) from exc

    candidate, is_duplicate = await service.create_candidate(
        db,
        job_posting_id=job_id,
        full_name=form.full_name,
        email=form.email,
        phone=form.phone,
        cv_file=cv_file,
        certificate_files=certificate_files,
        assessment_input=parsed_assessment,
    )

    # Async — parsing must never block the upload response (brief §7).
    parse_candidate_documents.delay(str(candidate.id))

    return CandidateCreateResponse(**CandidateOut.model_validate(candidate).model_dump(), duplicate_warning=is_duplicate)


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateListItemOut])
def list_candidates(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CandidateListItemOut]:
    candidates = service.list_candidates(db, job_id)
    scores = matching_service.get_latest_scores_for_job(db, [c.id for c in candidates])

    items = []
    for c in candidates:
        base = CandidateOut.model_validate(c).model_dump()
        score = scores.get(c.id)
        items.append(
            CandidateListItemOut(
                **base,
                final_score=float(score.final_score) if score else None,
                label=score.label.value if score else None,
                score_computed_at=score.computed_at if score else None,
            )
        )
    # FR-6.1: default sort highest score first; unscored candidates last.
    items.sort(key=lambda i: (i.final_score is None, -(i.final_score or 0)))
    return items


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Candidate:
    return service.get_candidate(db, candidate_id)


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def update_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> Candidate:
    updated = service.update_candidate(db, candidate_id, payload)
    fields_set = payload.model_dump(exclude_unset=True)
    if "parsed_profile" in fields_set or "assessment_input" in fields_set:
        # A correction to either input invalidates the previous score.
        compute_candidate_score.delay(str(candidate_id))
    return updated


@router.patch("/candidates/{candidate_id}/status", response_model=CandidateOut)
def update_candidate_status(
    candidate_id: uuid.UUID,
    payload: CandidateStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "recruiter", "hiring_manager")),
) -> Candidate:
    return service.update_status(db, candidate_id, payload.status, payload.reason, current_user)


@router.post("/candidates/{candidate_id}/score", status_code=status.HTTP_202_ACCEPTED)
def trigger_score(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> dict:
    """Re-trigger scoring (async) — e.g. after a manual correction to the
    parsed profile or assessment_input."""
    service.get_candidate(db, candidate_id)  # 404s early if the id is bad
    compute_candidate_score.delay(str(candidate_id))
    return {"detail": "Perhitungan skor dijadwalkan"}


@router.get("/candidates/{candidate_id}/score", response_model=CandidateScoreOut)
def get_score(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return matching_service.get_latest_score(db, candidate_id)
