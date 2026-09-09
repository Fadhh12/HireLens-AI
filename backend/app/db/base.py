"""
SQLAlchemy declarative base. Every model in modules/*/model.py imports
`Base` from here so Alembic's autogenerate can discover all tables
from one place (see migrations/env.py).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
