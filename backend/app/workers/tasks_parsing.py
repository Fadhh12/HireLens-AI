"""Background task: parse one candidate's CV (FR-4, FR-3.5).

Runs via FastAPI's BackgroundTasks (in-process, after the response is
sent) rather than a separate Celery worker — see app/workers/__init__.py
for why. Opens its own DB session since it doesn't run inside a request's
dependency-injected one.
"""

import logging

from app.db.session import SessionLocal
from app.modules.candidates import service as candidates_service

logger = logging.getLogger(__name__)


def parse_candidate_documents(candidate_id: str) -> None:
    from app.modules.document_ai.service import parse_candidate_cv
    from app.workers.tasks_scoring import compute_candidate_score

    db = SessionLocal()
    try:
        candidate = candidates_service.get_candidate(db, candidate_id)
        try:
            profile = parse_candidate_cv(candidate.cv_file_url, candidate.cv_file_url)
        except Exception as exc:
            # FR-3.5: parsing failed outright -> needs_manual_review, never
            # a rejected/lost candidate. Broad except is deliberate — any
            # failure mode here (corrupt file, unsupported type, storage
            # download error) gets the same safe fallback.
            logger.warning("CV parsing failed for candidate %s: %s", candidate_id, exc)
            candidates_service.mark_needs_manual_review(db, candidate_id, reason=str(exc))
        else:
            candidates_service.apply_parsed_profile(db, candidate_id, profile)
    finally:
        db.close()

    # Chained regardless of parse outcome — PRD's "upload -> muncul di
    # ranking < 30 detik" metric implies a score should exist right after
    # intake even if parsing came up empty (skill_fit just scores low,
    # which is itself informative rather than leaving no score row at all).
    # Direct call rather than another add_task hop — we're already running
    # off the request/response path, so there's nothing to gain by
    # scheduling a second background task instead of just calling on.
    compute_candidate_score(candidate_id)
