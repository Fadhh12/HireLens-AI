"""Candidate intake/list/detail/status endpoints (FR-3, FR-6, FR-7). Phase 3-4."""

from fastapi import APIRouter

router = APIRouter(tags=["candidates"])

# TODO(Phase 3): POST /jobs/{job_id}/candidates (multipart upload)
# TODO(Phase 3): GET /jobs/{job_id}/candidates (list + filter + sort)
# TODO(Phase 4): GET /candidates/{id}, PATCH /candidates/{id}, PATCH /candidates/{id}/status
