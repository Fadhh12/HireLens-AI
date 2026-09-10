"""API-level tests for the scoring endpoints + score-augmented candidate
list (FR-5, FR-6.1). LLM is mocked out — mock_llm fixture."""

import io
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth import service as auth_service
from app.modules.auth.model import UserRole
from app.modules.auth.schema import UserCreate
from app.modules.candidates.model import Candidate, CandidateStatus
from app.modules.jobs import service as jobs_service
from app.modules.jobs.model import JobLevel, JobStatus
from app.modules.jobs.schema import JobPostingCreate
from app.modules.matching_engine import service as matching_service


def _admin_token(client: TestClient, db_session: Session) -> str:
    auth_service.create_user(
        db_session, UserCreate(name="Admin", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.admin)
    )
    resp = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    return resp.json()["access_token"]


def _make_job(db_session: Session, **overrides):
    payload = dict(
        title="Backend Engineer",
        department="Eng",
        required_skills=["Python"],
        level=JobLevel.mid,
        status=JobStatus.active,
        min_experience_years=1,
    )
    payload.update(overrides)
    return jobs_service.create_job(db_session, JobPostingCreate(**payload), created_by=uuid.uuid4())


def _make_candidate(db_session: Session, job_id, **overrides) -> Candidate:
    candidate = Candidate(
        id=uuid.uuid4(),
        job_posting_id=job_id,
        full_name="Test Candidate",
        email="test@example.com",
        phone="0812345678",
        cv_file_url="candidates/fake/cv.pdf",
        certificate_urls=[],
        parsed_profile={
            "skills": {"value": ["Python"], "verified": False},
            "experience_years": {"value": 2.0, "verified": False},
        },
        status=CandidateStatus.new,
    )
    for k, v in overrides.items():
        setattr(candidate, k, v)
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate


def test_trigger_score_enqueues_task(client, db_session, mock_score_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id)

    resp = client.post(
        f"/api/v1/candidates/{candidate.id}/score", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 202
    assert str(candidate.id) in mock_score_task


def test_get_score_404_before_computed(client, db_session):
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id)

    resp = client.get(f"/api/v1/candidates/{candidate.id}/score", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_compute_and_save_score_end_to_end(client, db_session, mock_llm):
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id)

    # Directly call the service (equivalent of what the background task
    # does) rather than going through a real BackgroundTasks dispatch.
    matching_service.compute_and_save_score(db_session, candidate.id)

    resp = client.get(f"/api/v1/candidates/{candidate.id}/score", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["final_score"] > 0
    assert body["label"] in {"strong_match", "consider", "not_a_fit"}
    assert body["model_version"].startswith("matching-engine-v1.0")
    assert "llm-unavailable" in body["model_version"]  # mock_llm simulates no LLM
    assert body["score_breakdown"]["skill_fit"]["matched_required"] == ["python"]


def test_update_candidate_correction_retriggers_score(client, db_session, mock_score_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id)
    headers = {"Authorization": f"Bearer {token}"}

    # A correction that doesn't touch parsed_profile/assessment_input -> no retrigger.
    client.patch(f"/api/v1/candidates/{candidate.id}", headers=headers, json={"full_name": "New Name"})
    assert mock_score_task == []

    # A correction to parsed_profile -> retriggers.
    client.patch(
        f"/api/v1/candidates/{candidate.id}",
        headers=headers,
        json={"parsed_profile": {"skills": {"value": ["Python", "SQL"], "verified": True}}},
    )
    assert str(candidate.id) in mock_score_task


def test_candidate_list_includes_latest_score_and_sorts_desc(client, db_session, mock_llm):
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    weak = _make_candidate(
        db_session, job.id, email="weak@example.com",
        parsed_profile={"skills": {"value": [], "verified": False}, "experience_years": {"value": 0, "verified": False}},
    )
    strong = _make_candidate(
        db_session, job.id, email="strong@example.com",
        parsed_profile={"skills": {"value": ["Python"], "verified": False}, "experience_years": {"value": 5, "verified": False}},
    )

    matching_service.compute_and_save_score(db_session, weak.id)
    matching_service.compute_and_save_score(db_session, strong.id)

    resp = client.get(f"/api/v1/jobs/{job.id}/candidates", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    # Highest score first (FR-6.1).
    assert body[0]["email"] == "strong@example.com"
    assert body[0]["final_score"] >= body[1]["final_score"]


def test_candidate_list_handles_unscored_candidates(client, db_session):
    """A candidate with no score row yet (still parsing) shouldn't 500 the list."""
    token = _admin_token(client, db_session)
    job = _make_job(db_session)
    _make_candidate(db_session, job.id)

    resp = client.get(
        f"/api/v1/jobs/{job.id}/candidates", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()[0]["final_score"] is None
