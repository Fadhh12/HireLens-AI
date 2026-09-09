"""Celery task: generate one interview guide (FR-8.1, async per SDD §4)."""

import logging
import uuid

from app.db.session import SessionLocal
from app.modules.interview import service as interview_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="generate_interview_guide_task", bind=True, max_retries=0)
def generate_interview_guide_task(self, candidate_id: str, actor_id: str) -> None:
    db = SessionLocal()
    try:
        interview_service.generate_guide(db, uuid.UUID(candidate_id), uuid.UUID(actor_id))
    except Exception as exc:
        # No rule-based fallback exists for question generation (unlike
        # scoring) — a failure here just means no new guide version this
        # attempt; the candidate keeps whatever earlier version existed.
        logger.warning("Interview guide generation failed for candidate %s: %s", candidate_id, exc)
    finally:
        db.close()
