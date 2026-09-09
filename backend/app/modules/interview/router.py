"""Interview guide endpoints: generate/get/edit (FR-8, BR-4). Phase 5."""

from fastapi import APIRouter

router = APIRouter(tags=["interview"])

# TODO(Phase 5): POST /candidates/{id}/interview-guide (async, only if status >= shortlisted per BR-4)
# TODO(Phase 5): GET /candidates/{id}/interview-guide, PATCH /interview-guide/{guide_id}
