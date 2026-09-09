"""Celery app instance — parsing (Phase 3) and scoring (Phase 4) run here,
never inline in a request handler (brief §7: never call LLM/parsing
synchronously)."""

from celery import Celery

from app.core.config import get_settings

# Import every model so SQLAlchemy can resolve cross-table foreign keys
# (e.g. candidates.job_posting_id -> job_postings.id) when a task runs.
# The worker process only imports what celery_app's `include` pulls in —
# unlike the FastAPI app, nothing else eagerly imports the full module
# graph here, so this has to be explicit.
from app.modules.auth import model as _auth_model  # noqa: F401
from app.modules.jobs import model as _jobs_model  # noqa: F401
from app.modules.candidates import model as _candidates_model  # noqa: F401
from app.modules.matching_engine import model as _matching_engine_model  # noqa: F401

settings = get_settings()

celery_app = Celery(
    "hirelens",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks_parsing", "app.workers.tasks_scoring"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)
