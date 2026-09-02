from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.repositories.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

database_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
config.set_main_option("sqlalchemy.url", database_url)
target_metadata = Base.metadata


def configure(connection=None, *, literal_binds=False):
    context.configure(
        connection=connection,
        url=None if connection else database_url,
        target_metadata=target_metadata,
        literal_binds=literal_binds,
        compare_type=True,
        version_table="alembic_version_leadtools",
    )


def run_migrations_offline():
    configure(literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        configure(connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
