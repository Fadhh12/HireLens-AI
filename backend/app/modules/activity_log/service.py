"""Activity log recording + querying (FR-7.3, UI/UX Layar 10)."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity_log.model import ActivityLog
from app.modules.activity_log.schema import ActivityLogOut
from app.modules.auth.model import User


def log_activity(
    db: Session,
    actor_id: uuid.UUID,
    action: str,
    candidate_id: uuid.UUID | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        id=uuid.uuid4(),
        candidate_id=candidate_id,
        actor_id=actor_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_activity_logs(
    db: Session,
    actor_id: uuid.UUID | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 200,
) -> list[ActivityLogOut]:
    """UI/UX Layar 10 filters: date range, actor, action type."""
    query = (
        select(ActivityLog, User.name)
        .join(User, User.id == ActivityLog.actor_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    if actor_id is not None:
        query = query.where(ActivityLog.actor_id == actor_id)
    if action is not None:
        query = query.where(ActivityLog.action == action)
    if date_from is not None:
        query = query.where(ActivityLog.created_at >= date_from)
    if date_to is not None:
        query = query.where(ActivityLog.created_at <= date_to)

    rows = db.execute(query).all()
    return [
        ActivityLogOut(
            id=log.id,
            candidate_id=log.candidate_id,
            actor_id=log.actor_id,
            actor_name=actor_name,
            action=log.action,
            old_value=log.old_value,
            new_value=log.new_value,
            created_at=log.created_at,
        )
        for log, actor_name in rows
    ]
