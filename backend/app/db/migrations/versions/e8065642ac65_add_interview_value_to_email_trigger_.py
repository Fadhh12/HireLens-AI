"""add interview value to email_trigger enum

Revision ID: e8065642ac65
Revises: bfc8831de65e
Create Date: 2026-09-12 19:18:13.538015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8065642ac65'
down_revision: Union[str, None] = 'bfc8831de65e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE email_trigger ADD VALUE IF NOT EXISTS 'interview'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums — removing one cleanly means
    # recreating the type and every column using it. Not worth the risk
    # for a purely additive change; downgrading past this revision would
    # need a manual DBA step if ever actually required.
    pass
