"""
Alembic Environment Configuration.

Configures Alembic migrations to run asynchronously with the project's declarative base
and settings-managed database URL.
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import application configuration and declarative Base metadata
from src.core.config import settings
from src.database.base import Base
import src.models # Load all models for metadata

# retrieve Alembic configuration object
config = context.config

# Setup Python logging formatters
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Expose model metadata for migration autogeneration support
target_metadata = Base.metadata

# Retrieve and set database connection URL dynamically from global settings
escaped_url = settings.DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    Generates SQL script outputs directly without opening database connections.
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


def do_run_migrations(connection) -> None:
    """
    Executes actual migration scripts synchronously inside an active connection scope.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    Creates an asynchronous engine and runs sync execution tasks over the connection.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
