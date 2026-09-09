"""API/unit tests for interview guide generation (FR-8, BR-4)."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth import service as auth_service
from app.modules.auth.model import UserRole
from app.modules.auth.schema import UserCreate
from app.modules.candidates.model import Candidate, CandidateStatus
from app.modules.interview import service as interview_service
from app.modules.jobs import service as jobs_service
from app.modules.jobs.model import JobLevel, JobStatus
from app.modules.jobs.schema import JobPostingCreate


def _admin_token(client: TestClient, db_session: Session) -> str:
    auth_service.create_user(
        db_session, UserCreate(name="Admin", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.admin)
    )
    resp = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    return resp.json()["access_token"]


def _make_job(db_session: Session):
    return jobs_service.create_job(
        db_session,
        JobPostingCreate(title="Backend Engineer", department="Eng", required_skills=["Python"], level=JobLevel.mid, status=JobStatus.active),
        created_by=uuid.uuid4(),
    )


def _make_candidate(db_session: Session, job_id, status: CandidateStatus) -> Candidate:
    candidate = Candidate(
        id=uuid.uuid4(),
        job_posting_id=job_id,
        full_name="Test Candidate",
        email="test@example.com",
        phone="0812345678",
        cv_file_url="candidates/fake/cv.pdf",
        certificate_urls=[],
        parsed_profile={"skills": {"value": ["Python"], "verified": False}},
        status=status,
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate


def test_generate_guide_blocked_before_shortlisted(db_session, mock_question_generator):
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id, CandidateStatus.new)
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as exc:
        interview_service.generate_guide(db_session, candidate.id, uuid.uuid4())
    assert exc.value.status_code == 409


def test_generate_guide_succeeds_when_shortlisted(db_session, mock_question_generator):
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id, CandidateStatus.shortlisted)
    actor_id = uuid.uuid4()

    guide = interview_service.generate_guide(db_session, candidate.id, actor_id)
    assert guide.version == 1
    assert len(guide.technical_questions) == 3
    assert guide.is_final is False


def test_regenerate_creates_new_version_not_overwrite(db_session, mock_question_generator):
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id, CandidateStatus.shortlisted)
    actor_id = uuid.uuid4()

    v1 = interview_service.generate_guide(db_session, candidate.id, actor_id)
    v2 = interview_service.generate_guide(db_session, candidate.id, actor_id)

    assert v1.version == 1
    assert v2.version == 2
    versions = interview_service.list_guide_versions(db_session, candidate.id)
    assert len(versions) == 2
    latest = interview_service.get_latest_guide(db_session, candidate.id)
    assert latest.id == v2.id


def test_finalized_guide_cannot_be_edited(db_session, mock_question_generator):
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id, CandidateStatus.shortlisted)
    guide = interview_service.generate_guide(db_session, candidate.id, uuid.uuid4())
    interview_service.finalize_guide(db_session, guide.id)

    from fastapi import HTTPException
    import pytest
    from app.modules.interview.schema import InterviewGuideUpdate

    with pytest.raises(HTTPException) as exc:
        interview_service.update_guide(db_session, guide.id, InterviewGuideUpdate(risk_areas=["new"]))
    assert exc.value.status_code == 409


def test_generate_guide_api_rejects_ineligible_status_synchronously(client: TestClient, db_session, mock_question_generator):
    """Regression test: the endpoint must validate BR-4 before enqueueing
    (previously always returned 202 regardless of status, silently
    dropping ineligible requests inside the async task with no feedback)."""
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id, CandidateStatus.new)

    resp = client.post(
        f"/api/v1/candidates/{candidate.id}/interview-guide",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


def test_generate_guide_api_role_guard(client: TestClient, db_session):
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id, CandidateStatus.shortlisted)

    # recruiter is NOT allowed to generate (SRS §2: interviewer-owned feature)
    auth_service.create_user(
        db_session,
        UserCreate(name="Recruiter", email="recruiter@hirelens.ai", password="Passw0rd", role=UserRole.recruiter),
    )
    recruiter_login = client.post("/api/v1/auth/login", json={"email": "recruiter@hirelens.ai", "password": "Passw0rd"})
    recruiter_token = recruiter_login.json()["access_token"]

    resp = client.post(
        f"/api/v1/candidates/{candidate.id}/interview-guide",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == 403
