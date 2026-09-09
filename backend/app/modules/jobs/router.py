"""Job posting endpoints: CRUD + /close (FR-2).

Read access (list/get) is open to any authenticated role — Hiring
Manager and Interviewer need job context even though they can't create
or edit one. Write access (create/update/close) is Admin + Recruiter,
per SRS §2's role matrix ("Buat job" listed only under those two).
"""

import uuid

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.jobs import service
from app.modules.jobs.model import JobPosting, JobStatus
from app.modules.jobs.schema import JobPostingCreate, JobPostingOut, JobPostingUpdate
from sqlalchemy.orm import Session

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobPostingOut])
def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[JobPosting]:
    return service.list_jobs(db, status_filter)


@router.post("", response_model=JobPostingOut, status_code=201)
def create_job(
    payload: JobPostingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "recruiter")),
) -> JobPosting:
    return service.create_job(db, payload, created_by=current_user.id)


@router.get("/{job_id}", response_model=JobPostingOut)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> JobPosting:
    return service.get_job(db, job_id)


@router.patch("/{job_id}", response_model=JobPostingOut)
def update_job(
    job_id: uuid.UUID,
    payload: JobPostingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> JobPosting:
    return service.update_job(db, job_id, payload)


@router.post("/{job_id}/close", response_model=JobPostingOut)
def close_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "recruiter")),
) -> JobPosting:
    return service.close_job(db, job_id)
