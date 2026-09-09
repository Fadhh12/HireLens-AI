"""API-level tests: login endpoint, role guard on /users (FR-1, SRS §2)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.auth import service
from app.modules.auth.model import UserRole
from app.modules.auth.schema import UserCreate


def _seed_admin(db_session: Session):
    return service.create_user(
        db_session,
        UserCreate(name="Admin", email="admin@hirelens.ai", password="Passw0rd", role=UserRole.admin),
    )


def _seed_recruiter(db_session: Session):
    return service.create_user(
        db_session,
        UserCreate(name="Recruiter", email="recruiter@hirelens.ai", password="Passw0rd", role=UserRole.recruiter),
    )


def test_login_returns_tokens(client: TestClient, db_session: Session) -> None:
    _seed_admin(db_session)
    resp = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_wrong_password(client: TestClient, db_session: Session) -> None:
    _seed_admin(db_session)
    resp = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "nope12345"})
    assert resp.status_code == 401


def test_users_endpoint_requires_admin_role(client: TestClient, db_session: Session) -> None:
    _seed_recruiter(db_session)
    login = client.post("/api/v1/auth/login", json={"email": "recruiter@hirelens.ai", "password": "Passw0rd"})
    token = login.json()["access_token"]

    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_users_endpoint_allows_admin(client: TestClient, db_session: Session) -> None:
    _seed_admin(db_session)
    login = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    token = login.json()["access_token"]

    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_logout_invalidates_access_token(client: TestClient, db_session: Session) -> None:
    _seed_admin(db_session)
    login = client.post("/api/v1/auth/login", json={"email": "admin@hirelens.ai", "password": "Passw0rd"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    # Same access token must now be rejected (token_version bumped).
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
