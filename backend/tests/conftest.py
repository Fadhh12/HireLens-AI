"""Shared test fixtures. Auth/DB tests run against an in-memory SQLite
DB (via dependency override) — never against the real Supabase DB."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Import every model so Base.metadata knows about their tables.
from app.modules.auth import model as _auth_model  # noqa: F401
from app.modules.jobs import model as _jobs_model  # noqa: F401


@pytest.fixture()
def db_session():
    # StaticPool keeps a single connection alive for the engine's lifetime —
    # without it, each checkout from the pool gets its own throwaway
    # in-memory SQLite database and "no such table" follows.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
