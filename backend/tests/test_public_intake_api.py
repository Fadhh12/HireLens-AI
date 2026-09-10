"""API-level tests for the public intake bridge (POST /public/apply) —
the Google Form/Apps Script channel, user-requested test feature. Auth
here is a static API key (X-API-Key), not a JWT."""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import dependencies as deps
from app.modules.jobs import service as jobs_service
from app.modules.jobs.model import JobLevel, JobStatus
from app.modules.jobs.schema import JobPostingCreate

API_KEY = "test-public-apply-key"


@pytest.fixture()
def api_key_configured(monkeypatch: pytest.MonkeyPatch):
    """Points require_api_key at a known key instead of the real (empty in
    tests) settings value, so the endpoint doesn't 503 by default."""

    class _FakeSettings:
        public_apply_api_key = API_KEY

    monkeypatch.setattr(deps, "get_settings", lambda: _FakeSettings())


def _make_job(db_session: Session, **overrides):
    import uuid

    payload = dict(
        title="Junior Frontend", department="IT", required_skills=["React"], level=JobLevel.junior
    )
    payload.update(overrides)
    return jobs_service.create_job(db_session, JobPostingCreate(**payload), created_by=uuid.uuid4())


def _pdf_bytes() -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test Applicant")
    page.insert_text((50, 70), "applicant@example.com")
    data = doc.tobytes()
    doc.close()
    return data


def _apply(client: TestClient, *, headers=None, **data):
    return client.post(
        "/api/v1/public/apply",
        headers=headers or {},
        data={"job_title": "Junior Frontend", "full_name": "Test Applicant", "email": "applicant@example.com", "phone": "0812345678", **data},
        files={"cv_file": ("cv.pdf", io.BytesIO(_pdf_bytes()), "application/pdf")},
    )


def test_public_apply_disabled_without_configured_key(
    client, db_session, mock_storage, mock_parse_task, monkeypatch: pytest.MonkeyPatch
):
    """Explicitly force an empty key rather than relying on the fixture's
    absence — backend/.env may itself have PUBLIC_APPLY_API_KEY set on a dev
    machine, which would otherwise make this test see a real key and assert
    the wrong thing (401 instead of 503)."""

    class _FakeSettings:
        public_apply_api_key = ""

    monkeypatch.setattr(deps, "get_settings", lambda: _FakeSettings())

    _make_job(db_session, status=JobStatus.active)
    resp = _apply(client, headers={"X-API-Key": "anything"})
    assert resp.status_code == 503


def test_public_apply_success(client, db_session, mock_storage, mock_parse_task, api_key_configured):
    _make_job(db_session, status=JobStatus.active)
    resp = _apply(client, headers={"X-API-Key": API_KEY})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "new"
    assert body["full_name"] == "Test Applicant"
    assert len(mock_storage) == 1
    assert len(mock_parse_task) == 1


def test_public_apply_rejects_missing_key(client, db_session, mock_storage, mock_parse_task, api_key_configured):
    _make_job(db_session, status=JobStatus.active)
    resp = _apply(client)
    assert resp.status_code == 401


def test_public_apply_rejects_wrong_key(client, db_session, mock_storage, mock_parse_task, api_key_configured):
    _make_job(db_session, status=JobStatus.active)
    resp = _apply(client, headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_public_apply_unknown_job_title(client, db_session, mock_storage, mock_parse_task, api_key_configured):
    resp = _apply(client, headers={"X-API-Key": API_KEY}, job_title="Nonexistent Role")
    assert resp.status_code == 404


def test_public_apply_rejected_on_closed_job(client, db_session, mock_storage, mock_parse_task, api_key_configured):
    _make_job(db_session, status=JobStatus.closed)
    resp = _apply(client, headers={"X-API-Key": API_KEY})
    assert resp.status_code == 409
