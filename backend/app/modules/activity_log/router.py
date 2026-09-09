"""GET /activity-logs — Admin only (UI/UX Layar 10)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.activity_log import service
from app.modules.activity_log.schema import ActivityLogOut
from app.modules.auth.model import User

router = APIRouter(prefix="/activity-logs", tags=["activity-log"])


@router.get("", response_model=list[ActivityLogOut])
def list_activity_logs(
    actor_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> list[ActivityLogOut]:
    return service.list_activity_logs(db, actor_id, action, date_from, date_to)
