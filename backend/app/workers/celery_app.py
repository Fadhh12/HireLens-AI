"""Celery app instance, configured from CELERY_BROKER_URL / CELERY_RESULT_BACKEND.
Wired up in Phase 3 alongside candidate intake (parsing must be async, never
block the upload request — see brief §7)."""

# TODO(Phase 3): celery_app = Celery("hirelens", broker=..., backend=...)
