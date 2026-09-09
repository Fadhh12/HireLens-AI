"""Job posting endpoints: CRUD + /close (FR-2). Phase 2."""

from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])

# TODO(Phase 2): GET /jobs, POST /jobs, GET /jobs/{id}, PATCH /jobs/{id}, POST /jobs/{id}/close
