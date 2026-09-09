"""API-level tests for candidate intake (FR-3, FR-2.4, SRS §7, SRS §4)."""

import io

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth import service as auth_service
from app.modules.auth.model import UserRole
from app.modules.auth.schema import UserCreate
from app.modules.jobs import service as jobs_service
from app.modules.jobs.model import JobLevel, JobStatus
from app.modules.jobs.schema import JobPostingCreate


def _admin_token(client: TestClient, db_session: Session) -> str:
    auth_service.create_user(
        db_session, UserCreate(name="Admin", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.admin)
    )
    resp = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    return resp.json()["access_token"]


def _make_job(db_session: Session, **overrides):
    payload = dict(title="Backend Engineer", department="Eng", required_skills=["Python"], level=JobLevel.mid)
    payload.update(overrides)
    import uuid

    return jobs_service.create_job(db_session, JobPostingCreate(**payload), created_by=uuid.uuid4())


def _pdf_bytes() -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test Candidate")
    page.insert_text((50, 70), "test.candidate@example.com")
    page.insert_text((50, 90), "0812345678")
    data = doc.tobytes()
    doc.close()
    return data


def test_intake_candidate_persists_assessment_input(client, db_session, mock_storage, mock_parse_task):
    """Regression test: assessment_input (FR-3.3) was collected by the intake
    form but never reached the backend — the form field was missing from
    the endpoint signature and the frontend never appended it either."""
    import json

    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)

    assessment = {"mbti": "INTJ", "competency_scores": {"communication": 4, "leadership": 3}}
    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "full_name": "Test Candidate",
            "email": "test.candidate@example.com",
            "phone": "0812345678",
            "assessment_input": json.dumps(assessment),
        },
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["assessment_input"] == assessment


def test_intake_candidate_success(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)

    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={"full_name": "Test Candidate", "email": "test.candidate@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "new"
    assert body["duplicate_warning"] is False
    assert len(mock_storage) == 1  # one file uploaded
    assert len(mock_parse_task) == 1  # parse task enqueued


def test_intake_duplicate_email_warns_but_still_creates(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)
    headers = {"Authorization": f"Bearer {token}"}
    files = {"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")}

    client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers=headers,
        data={"full_name": "A", "email": "dup@example.com", "phone": "0812345678"},
        files=files,
    )
    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers=headers,
        data={"full_name": "B", "email": "dup@example.com", "phone": "0812345679"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 201
    assert resp.json()["duplicate_warning"] is True


def test_intake_rejects_oversized_file(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)

    oversized = io.BytesIO(b"0" * (5 * 1024 * 1024 + 1))
    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={"full_name": "X", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", oversized, "application/pdf")},
    )
    assert resp.status_code == 422


def test_intake_rejects_wrong_file_type(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)

    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={"full_name": "X", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 422


def test_intake_rejects_invalid_phone(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)

    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={"full_name": "X", "email": "x@example.com", "phone": "abc"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 422  # not a 500 — this is the manual-validation bug regression test


def test_intake_accepts_formatted_international_phone(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)

    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={"full_name": "X", "email": "x@example.com", "phone": "+62 813-9988-7766"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 201


def test_intake_rejected_on_closed_job(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)
    jobs_service.close_job(db_session, job.id)

    resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers={"Authorization": f"Bearer {token}"},
        data={"full_name": "X", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    assert resp.status_code == 409


def test_list_and_get_candidate(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers=headers,
        data={"full_name": "X", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    candidate_id = create_resp.json()["id"]

    list_resp = client.get(f"/api/v1/jobs/{job.id}/candidates", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/v1/candidates/{candidate_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["full_name"] == "X"


def test_update_candidate_manual_correction(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers=headers,
        data={"full_name": "Typo Name", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    candidate_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/candidates/{candidate_id}", headers=headers, json={"full_name": "Corrected Name"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["full_name"] == "Corrected Name"


def test_update_status_requires_reason(client, db_session, mock_storage, mock_parse_task):
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers=headers,
        data={"full_name": "X", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    candidate_id = create_resp.json()["id"]

    missing_reason = client.patch(
        f"/api/v1/candidates/{candidate_id}/status", headers=headers, json={"status": "shortlisted"}
    )
    assert missing_reason.status_code == 422

    ok = client.patch(
        f"/api/v1/candidates/{candidate_id}/status",
        headers=headers,
        json={"status": "shortlisted", "reason": "Skill match kuat"},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "shortlisted"


def test_update_status_allows_backward_transition_with_reason(client, db_session, mock_storage, mock_parse_task):
    """BR-1: the system never regresses a status on its own, but a human
    can — as long as they say why."""
    token = _admin_token(client, db_session)
    job = _make_job(db_session, status=JobStatus.active)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        f"/api/v1/jobs/{job.id}/candidates",
        headers=headers,
        data={"full_name": "X", "email": "x@example.com", "phone": "0812345678"},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )
    candidate_id = create_resp.json()["id"]

    client.patch(
        f"/api/v1/candidates/{candidate_id}/status",
        headers=headers,
        json={"status": "hired", "reason": "Diterima"},
    )
    backward = client.patch(
        f"/api/v1/candidates/{candidate_id}/status",
        headers=headers,
        json={"status": "new", "reason": "Salah input, batal hire"},
    )
    assert backward.status_code == 200
    assert backward.json()["status"] == "new"
