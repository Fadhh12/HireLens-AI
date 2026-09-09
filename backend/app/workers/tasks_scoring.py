"""Celery task: compute one candidate's match score (FR-5). Chained
automatically after parsing finishes (tasks_parsing.py) and also
triggerable on demand via POST /candidates/{id}/score."""

import logging

from app.db.session import SessionLocal
from app.modules.matching_engine import service as matching_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="compute_candidate_score", bind=True, max_retries=0)
def compute_candidate_score(self, candidate_id: str) -> None:
    db = SessionLocal()
    try:
        matching_service.compute_and_save_score(db, candidate_id)
    except Exception as exc:
        # Scoring failure shouldn't crash the worker or lose the candidate —
        # it just means no score row exists yet; GET /score reports that
        # clearly and POST /score can be retried once the underlying issue
        # (e.g. a still-missing parsed_profile) is fixed.
        logger.warning("Scoring failed for candidate %s: %s", candidate_id, exc)
    finally:
        db.close()
