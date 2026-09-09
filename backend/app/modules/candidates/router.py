"""Candidate intake/list/detail endpoints (FR-3, FR-6 partial, FR-4.3)."""

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
    CandidateOut,
    CandidateUpdate,
)
from app.modules.jobs.model import JobStatus
from app.modules.jobs.service import get_job
from app.workers.tasks_parsing import parse_candidate_documents
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

    candidate, is_duplicate = await service.create_candidate(
        db,
        job_posting_id=job_id,
        full_name=form.full_name,
        email=form.email,
        phone=form.phone,
        cv_file=cv_file,
        certificate_files=certificate_files,
    )

    # Async — parsing must never block the upload response (brief §7).
    parse_candidate_documents.delay(str(candidate.id))

    return CandidateCreateResponse(**CandidateOut.model_validate(candidate).model_dump(), duplicate_warning=is_duplicate)


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateOut])
def list_candidates(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Candidate]:
    return service.list_candidates(db, job_id)


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
    return service.update_candidate(db, candidate_id, payload)
