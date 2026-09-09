"""Tests for PDF report export (FR-9.1/9.2)."""

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


def _admin_token(client: TestClient, db_session: Session) -> str:
    auth_service.create_user(
        db_session, UserCreate(name="Admin", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.admin)
    )
    resp = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    return resp.json()["access_token"]


def test_export_report_pdf_without_score(client: TestClient, db_session: Session):
    token = _admin_token(client, db_session)
    job = jobs_service.create_job(
        db_session,
        JobPostingCreate(title="Backend Engineer", department="Eng", required_skills=["Python"], level=JobLevel.mid, status=JobStatus.active),
        created_by=uuid.uuid4(),
    )
    candidate = Candidate(
        id=uuid.uuid4(), job_posting_id=job.id, full_name="Test Candidate", email="test@example.com",
        phone="0812345678", cv_file_url="candidates/fake/cv.pdf", certificate_urls=[], status=CandidateStatus.new,
    )
    db_session.add(candidate)
    db_session.commit()

    resp = client.get(
        f"/api/v1/candidates/{candidate.id}/report/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"  # valid PDF magic bytes


def test_export_report_pdf_with_score(client: TestClient, db_session: Session, mock_llm):
    from app.modules.matching_engine import service as matching_service

    token = _admin_token(client, db_session)
    job = jobs_service.create_job(
        db_session,
        JobPostingCreate(title="Backend Engineer", department="Eng", required_skills=["Python"], level=JobLevel.mid, status=JobStatus.active),
        created_by=uuid.uuid4(),
    )
    candidate = Candidate(
        id=uuid.uuid4(), job_posting_id=job.id, full_name="Test Candidate", email="test@example.com",
        phone="0812345678", cv_file_url="candidates/fake/cv.pdf", certificate_urls=[],
        parsed_profile={"skills": {"value": ["Python"], "verified": False}, "experience_years": {"value": 2, "verified": False}},
        status=CandidateStatus.new,
    )
    db_session.add(candidate)
    db_session.commit()
    matching_service.compute_and_save_score(db_session, candidate.id)

    resp = client.get(
        f"/api/v1/candidates/{candidate.id}/report/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"
