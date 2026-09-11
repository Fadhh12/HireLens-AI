import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Make `app` importable when Alembic is invoked from backend/ (alembic.ini's
# script_location points inside app/db/migrations, but imports below need
# the backend/ directory on sys.path).
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402

# Import every module's model so Base.metadata sees all tables before
# autogenerate runs. Uncomment as each model.py is implemented (Phase 2+).
from app.modules.auth import model as auth_model  # noqa: F401, E402
from app.modules.jobs import model as jobs_model  # noqa: F401, E402
from app.modules.candidates import model as candidates_model  # noqa: F401, E402
from app.modules.matching_engine import model as matching_engine_model  # noqa: F401, E402
from app.modules.interview import model as interview_model  # noqa: F401, E402
from app.modules.activity_log import model as activity_log_model  # noqa: F401, E402
from app.modules.scheduling import model as scheduling_model  # noqa: F401, E402
from app.modules.messaging import model as messaging_model  # noqa: F401, E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use DATABASE_URL from app settings (.env) instead of alembic.ini's
# hardcoded sqlalchemy.url, so one source of truth drives both the app
# and migrations.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
