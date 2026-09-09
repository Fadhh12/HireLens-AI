"""Tests for activity logging (FR-7.3) — wired into candidate status changes."""

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


def _make_candidate(db_session: Session, job_id) -> Candidate:
    candidate = Candidate(
        id=uuid.uuid4(), job_posting_id=job_id, full_name="Test Candidate", email="test@example.com",
        phone="0812345678", cv_file_url="candidates/fake/cv.pdf", certificate_urls=[], status=CandidateStatus.new,
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate


def test_status_change_writes_activity_log(client: TestClient, db_session: Session):
    token = _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id)

    client.patch(
        f"/api/v1/candidates/{candidate.id}/status",
        headers=headers,
        json={"status": "shortlisted", "reason": "Cocok banget"},
    )

    resp = client.get("/api/v1/activity-logs", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) == 1
    assert logs[0]["action"] == "status_changed"
    assert logs[0]["old_value"] == "new"
    assert "shortlisted" in logs[0]["new_value"]
    assert logs[0]["actor_name"] == "Admin"


def test_activity_log_requires_admin(client: TestClient, db_session: Session):
    auth_service.create_user(
        db_session, UserCreate(name="Rec", email="rec@hirelens.ai", password="Passw0rd", role=UserRole.recruiter)
    )
    login = client.post("/api/v1/auth/login", json={"email": "rec@hirelens.ai", "password": "Passw0rd"})
    token = login.json()["access_token"]

    resp = client.get("/api/v1/activity-logs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_activity_log_filters_by_action(client: TestClient, db_session: Session):
    token = _admin_token(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    job = _make_job(db_session)
    candidate = _make_candidate(db_session, job.id)

    client.patch(
        f"/api/v1/candidates/{candidate.id}/status",
        headers=headers,
        json={"status": "shortlisted", "reason": "x"},
    )
    resp = client.get("/api/v1/activity-logs?action=status_changed", headers=headers)
    assert len(resp.json()) == 1
    resp_empty = client.get("/api/v1/activity-logs?action=nonexistent_action", headers=headers)
    assert resp_empty.json() == []
