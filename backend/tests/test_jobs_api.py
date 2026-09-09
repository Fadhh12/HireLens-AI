"""API-level tests: role guard on job posting write endpoints (SRS §2)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth import service as auth_service
from app.modules.auth.model import UserRole
from app.modules.auth.schema import UserCreate


def _token_for(client: TestClient, db_session: Session, role: UserRole) -> str:
    email = f"{role.value}@hirelens.ai"
    auth_service.create_user(db_session, UserCreate(name=role.value, email=email, password="Passw0rd", role=role))
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Passw0rd"})
    return resp.json()["access_token"]


def _job_payload(**overrides):
    payload = {
        "title": "Backend Engineer",
        "department": "Engineering",
        "description": "Build things",
        "required_skills": ["Python"],
        "nice_to_have_skills": [],
        "min_experience_years": 2,
        "level": "mid",
        "weight_skill_fit": 50,
        "weight_experience_fit": 30,
        "weight_values_fit": 20,
        "status": "draft",
    }
    payload.update(overrides)
    return payload


def test_recruiter_can_create_job(client: TestClient, db_session: Session) -> None:
    token = _token_for(client, db_session, UserRole.recruiter)
    resp = client.post(
        "/api/v1/jobs", json=_job_payload(), headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Backend Engineer"


def test_hiring_manager_cannot_create_job(client: TestClient, db_session: Session) -> None:
    token = _token_for(client, db_session, UserRole.hiring_manager)
    resp = client.post(
        "/api/v1/jobs", json=_job_payload(), headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_hiring_manager_can_list_jobs(client: TestClient, db_session: Session) -> None:
    recruiter_token = _token_for(client, db_session, UserRole.recruiter)
    client.post("/api/v1/jobs", json=_job_payload(), headers={"Authorization": f"Bearer {recruiter_token}"})

    hm_token = _token_for(client, db_session, UserRole.hiring_manager)
    resp = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {hm_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_job_weight_validation_returns_422(client: TestClient, db_session: Session) -> None:
    token = _token_for(client, db_session, UserRole.admin)
    resp = client.post(
        "/api/v1/jobs",
        json=_job_payload(weight_skill_fit=50, weight_experience_fit=50, weight_values_fit=50),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_close_then_edit_is_rejected(client: TestClient, db_session: Session) -> None:
    token = _token_for(client, db_session, UserRole.admin)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/jobs", json=_job_payload(status="active"), headers=headers).json()

    close_resp = client.post(f"/api/v1/jobs/{created['id']}/close", headers=headers)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    edit_resp = client.patch(f"/api/v1/jobs/{created['id']}", json={"title": "New"}, headers=headers)
    assert edit_resp.status_code == 409
