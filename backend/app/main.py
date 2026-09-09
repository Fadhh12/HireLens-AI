"""FastAPI entrypoint. Phase 0: skeleton + /health only. Routers are
included here as each module gets built out (auth in Phase 1, jobs in
Phase 2, candidates/interview from Phase 3 onward)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.auth.router import users_router
from app.modules.candidates.router import router as candidates_router
from app.modules.interview.router import router as interview_router
from app.modules.jobs.router import router as jobs_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


api_prefix = settings.api_v1_prefix
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(jobs_router, prefix=api_prefix)
app.include_router(candidates_router, prefix=api_prefix)
app.include_router(interview_router, prefix=api_prefix)
