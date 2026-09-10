"""Candidate intake/list/detail endpoints (FR-3, FR-6 partial, FR-4.3)."""

import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import ValidationError

from app.core.dependencies import get_current_user, require_api_key, require_role
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
from app.modules.jobs.model import JobPosting, JobStatus
from app.modules.jobs.service import get_job
from app.modules.matching_engine import service as matching_service
from app.modules.matching_engine.schema import CandidateScoreOut
from app.modules.candidates.report import build_candidate_report_pdf
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
    background_tasks: BackgroundTasks,
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
    background_tasks.add_task(parse_candidate_documents, str(candidate.id))

    return CandidateCreateResponse(**CandidateOut.model_validate(candidate).model_dump(), duplicate_warning=is_duplicate)


@router.post(
    "/public/apply",
    response_model=CandidateCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def public_apply(
    background_tasks: BackgroundTasks,
    job_title: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_key),
) -> CandidateCreateResponse:
    """Public candidate intake — the Google Form/Apps Script bridge (Task
    6.x, user-requested test channel). Auth is a static API key
    (require_api_key), not a JWT: the caller is a script running on Google's
    servers on an external applicant's behalf, not a logged-in HireLens user.

    Job is looked up by exact title (matches the Form's dropdown value)
    rather than by id, so the Apps Script config never has to carry a job's
    internal UUID — just the same title text a human sees in the dropdown.
    Everything past that point is identical to the authenticated intake
    path: same validation, same real parser + real scorer via
    BackgroundTasks, same duplicate-email warning.
    """
    job = db.query(JobPosting).filter(JobPosting.title == job_title).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_title}' tidak ditemukan")
    if job.status != JobStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job posting ini sudah tidak menerima kandidat baru (FR-2.4)",
        )

    try:
        form = CandidateIntakeForm(full_name=full_name, email=email, phone=phone)
    except ValidationError as exc:
        messages = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=messages) from exc

    candidate, is_duplicate = await service.create_candidate(
        db,
        job_posting_id=job.id,
        full_name=form.full_name,
        email=form.email,
        phone=form.phone,
        cv_file=cv_file,
        certificate_files=[],
        assessment_input=None,
    )

    background_tasks.add_task(parse_candidate_documents, str(candidate.id))

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


@router.get("/candidates/{candidate_id}/report/pdf")
def export_candidate_report(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    """FR-9.1/9.2: candidate summary + score as PDF, disclaimer included."""
    candidate = service.get_candidate(db, candidate_id)
    job = get_job(db, candidate.job_posting_id)
    try:
        score = matching_service.get_latest_score(db, candidate_id)
    except HTTPException:
        score = None

    pdf_bytes = build_candidate_report_pdf(candidate, job, score)
    filename = f"laporan-{candidate.full_name.replace(' ', '-').lower()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> Candidate:
    updated = service.update_candidate(db, candidate_id, payload)
    fields_set = payload.model_dump(exclude_unset=True)
    if "parsed_profile" in fields_set or "assessment_input" in fields_set:
        # A correction to either input invalidates the previous score.
        background_tasks.add_task(compute_candidate_score, str(candidate_id))
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> dict:
    """Re-trigger scoring (async) — e.g. after a manual correction to the
    parsed profile or assessment_input."""
    service.get_candidate(db, candidate_id)  # 404s early if the id is bad
    background_tasks.add_task(compute_candidate_score, str(candidate_id))
    return {"detail": "Perhitungan skor dijadwalkan"}


@router.get("/candidates/{candidate_id}/score", response_model=CandidateScoreOut)
def get_score(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return matching_service.get_latest_score(db, candidate_id)
