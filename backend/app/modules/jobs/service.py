"""Job posting business logic (FR-2, BR-2).

BR-2 in the docs says closed jobs can't have their *scoring criteria*
edited ("tidak dapat diedit kriteria scoring-nya"). We lock the whole
job on PATCH once closed, not just the criteria fields — closed is
meant to be a terminal, historical state (FR-2.4 already makes its
candidates read-only), and a partial-lock rule (some fields editable,
others not) is more surface area for inconsistency than a portfolio
project's audit story needs. Flagged as an interpretation, not silently
assumed.
"""

import uuid

from fastapi import HTTPException, status as http_status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.jobs.model import JobPosting, JobStatus
from app.modules.jobs.schema import (
    JobPostingCreate,
    JobPostingUpdate,
    _check_active_needs_required_skill,
    _check_weight_sum,
)


def create_job(db: Session, data: JobPostingCreate, created_by: uuid.UUID) -> JobPosting:
    job = JobPosting(id=uuid.uuid4(), created_by=created_by, **data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_jobs(db: Session, status_filter: JobStatus | None = None) -> list[JobPosting]:
    query = select(JobPosting).order_by(JobPosting.created_at.desc())
    if status_filter is not None:
        query = query.where(JobPosting.status == status_filter)
    return list(db.scalars(query))


def get_job(db: Session, job_id: uuid.UUID) -> JobPosting:
    job = db.get(JobPosting, job_id)
    if job is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Job posting tidak ditemukan")
    return job


def update_job(db: Session, job_id: uuid.UUID, data: JobPostingUpdate) -> JobPosting:
    job = get_job(db, job_id)
    if job.status == JobStatus.closed:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Job posting yang sudah closed tidak dapat diedit (BR-2)",
        )

    updates = data.model_dump(exclude_unset=True)

    # Validate the post-merge state, not just the fields being changed —
    # a payload that only touches `status` still needs to satisfy FR-2.2
    # against whatever required_skills the job already has.
    new_skill_w = float(updates.get("weight_skill_fit", job.weight_skill_fit))
    new_exp_w = float(updates.get("weight_experience_fit", job.weight_experience_fit))
    new_values_w = float(updates.get("weight_values_fit", job.weight_values_fit))
    try:
        _check_weight_sum(new_skill_w, new_exp_w, new_values_w)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    new_status = updates.get("status", job.status)
    new_required_skills = updates.get("required_skills", job.required_skills)
    try:
        _check_active_needs_required_skill(new_status, new_required_skills)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    for field, value in updates.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


def close_job(db: Session, job_id: uuid.UUID) -> JobPosting:
    """FR-2.4 / dedicated close action — one-way (no reopen endpoint exists)."""
    job = get_job(db, job_id)
    if job.status == JobStatus.closed:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Job posting sudah closed")
    job.status = JobStatus.closed
    db.commit()
    db.refresh(job)
    return job
