"""FastAPI entrypoint. Phase 0: skeleton + /health only. Routers are
included here as each module gets built out (auth in Phase 1, jobs in
Phase 2, candidates/interview from Phase 3 onward)."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.activity_log.router import router as activity_log_router
from app.modules.auth.router import router as auth_router
from app.modules.auth.router import users_router
from app.modules.candidates.router import router as candidates_router
from app.modules.interview.router import router as interview_router
from app.modules.jobs.router import router as jobs_router
from app.modules.messaging.router import router as messaging_router
from app.modules.messaging.service import poll_replies
from app.modules.scheduling.router import router as scheduling_router

settings = get_settings()
logger = logging.getLogger(__name__)

# How often the background loop below checks Gmail threads for a
# candidate reply. Not configurable via env — 10 minutes is a reasonable
# default for "notify HR a candidate replied", nothing here needs it tighter.
REPLY_POLL_INTERVAL_SECONDS = 600


async def _reply_poll_loop() -> None:
    """Best-effort periodic check (see messaging/service.py's poll_replies
    docstring on why this isn't a real-time push). Whether this loop
    actually keeps running for hours depends on the host process staying
    warm — POST /email-templates/poll-replies exists as a manual fallback
    in case this host scales the process down between requests."""
    while True:
        await asyncio.sleep(REPLY_POLL_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            found = await asyncio.to_thread(poll_replies, db)
            if found:
                logger.info("Background reply poll found %d new candidate reply(ies)", found)
        except Exception:  # noqa: BLE001 - must never kill the loop
            logger.exception("Background reply poll failed")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_reply_poll_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
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
app.include_router(activity_log_router, prefix=api_prefix)
app.include_router(scheduling_router, prefix=api_prefix)
app.include_router(messaging_router, prefix=api_prefix)
