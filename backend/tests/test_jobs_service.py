"""Unit tests for job posting business logic (FR-2, BR-2)."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.jobs import service
from app.modules.jobs.model import JobLevel, JobStatus
from app.modules.jobs.schema import JobPostingCreate, JobPostingUpdate


@pytest.fixture()
def created_by():
    return uuid.uuid4()


def _make_job(db_session: Session, created_by, **overrides):
    payload = dict(
        title="Backend Engineer",
        department="Engineering",
        description="",
        required_skills=["Python"],
        level=JobLevel.mid,
        status=JobStatus.draft,
    )
    payload.update(overrides)
    return service.create_job(db_session, JobPostingCreate(**payload), created_by=created_by)


def test_create_job_default_weights_sum_100(db_session: Session, created_by) -> None:
    job = _make_job(db_session, created_by)
    assert job.weight_skill_fit + job.weight_experience_fit + job.weight_values_fit == 100


def test_create_job_rejects_weights_not_summing_100() -> None:
    with pytest.raises(ValueError, match="100%"):
        JobPostingCreate(
            title="X",
            department="Y",
            level=JobLevel.junior,
            weight_skill_fit=50,
            weight_experience_fit=30,
            weight_values_fit=30,  # sums to 110
        )


def test_create_job_active_requires_required_skill() -> None:
    with pytest.raises(ValueError, match="skill wajib"):
        JobPostingCreate(
            title="X",
            department="Y",
            level=JobLevel.junior,
            required_skills=[],
            status=JobStatus.active,
        )


def test_update_job_rejects_weights_not_summing_100(db_session: Session, created_by) -> None:
    job = _make_job(db_session, created_by)
    with pytest.raises(HTTPException) as exc:
        service.update_job(db_session, job.id, JobPostingUpdate(weight_skill_fit=90))
    assert exc.value.status_code == 422


def test_update_job_can_rebalance_all_three_weights(db_session: Session, created_by) -> None:
    job = _make_job(db_session, created_by)
    updated = service.update_job(
        db_session,
        job.id,
        JobPostingUpdate(weight_skill_fit=40, weight_experience_fit=40, weight_values_fit=20),
    )
    assert float(updated.weight_skill_fit) == 40


def test_update_job_status_to_active_checks_existing_required_skills(
    db_session: Session, created_by
) -> None:
    job = _make_job(db_session, created_by, required_skills=[], status=JobStatus.draft)
    with pytest.raises(HTTPException) as exc:
        service.update_job(db_session, job.id, JobPostingUpdate(status=JobStatus.active))
    assert exc.value.status_code == 422


def test_closed_job_cannot_be_edited(db_session: Session, created_by) -> None:
    job = _make_job(db_session, created_by, status=JobStatus.active)
    service.close_job(db_session, job.id)
    with pytest.raises(HTTPException) as exc:
        service.update_job(db_session, job.id, JobPostingUpdate(title="New title"))
    assert exc.value.status_code == 409


def test_close_job_is_one_way(db_session: Session, created_by) -> None:
    job = _make_job(db_session, created_by, status=JobStatus.active)
    closed = service.close_job(db_session, job.id)
    assert closed.status == JobStatus.closed
    with pytest.raises(HTTPException) as exc:
        service.close_job(db_session, job.id)
    assert exc.value.status_code == 409


def test_list_jobs_filters_by_status(db_session: Session, created_by) -> None:
    _make_job(db_session, created_by, title="Draft Job", status=JobStatus.draft)
    _make_job(db_session, created_by, title="Active Job", status=JobStatus.active)

    active_only = service.list_jobs(db_session, JobStatus.active)
    assert [j.title for j in active_only] == ["Active Job"]
