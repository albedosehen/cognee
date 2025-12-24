import asyncio
import os
from alembic import context
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from cognee.infrastructure.databases.relational import get_relational_engine, Base
from cognee.infrastructure.databases.relational.config import get_relational_config

# Import all models to ensure they're registered with SQLAlchemy metadata
# Import them one by one to avoid circular dependencies
import cognee.modules.users.models.Principal
import cognee.modules.users.models.Permission
import cognee.modules.users.models.User
import cognee.modules.users.models.Tenant
import cognee.modules.users.models.Role
import cognee.modules.users.models.ACL
import cognee.modules.users.models.UserRole
import cognee.modules.users.models.UserTenant
import cognee.modules.users.models.UserDefaultPermissions
import cognee.modules.users.models.TenantDefaultPermissions
import cognee.modules.users.models.RoleDefaultPermissions
import cognee.modules.users.models.DatasetDatabase
import cognee.modules.data.models.Data
import cognee.modules.data.models.Dataset
import cognee.modules.data.models.DatasetData
import cognee.modules.data.models.GraphMetrics
import cognee.modules.data.models.graph_relationship_ledger
import cognee.modules.search.models.Query
import cognee.modules.search.models.Result
import cognee.modules.notebooks.models.Notebook
import cognee.modules.pipelines.models.PipelineRun
import cognee.modules.sync.models.SyncOperation
import cognee.modules.pipelines.models.Pipeline
import cognee.modules.pipelines.models.Task
import cognee.modules.pipelines.models.PipelineTask
import cognee.modules.pipelines.models.TaskRun

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


def configure_alembic():
    """Configure alembic with database connection at runtime, not import time."""
    # Ensure database directory exists before attempting to connect
    # This is critical for SQLite which cannot create the database file
    # if the parent directory doesn't exist
    relational_config = get_relational_config()
    if relational_config.db_provider == "sqlite" and relational_config.db_path:
        os.makedirs(relational_config.db_path, exist_ok=True)
        print(f"Ensured database directory exists: {relational_config.db_path}")

    db_engine = get_relational_engine()

    print("Using database:", db_engine.db_uri)

    config.set_section_option(
        config.config_ini_section,
        "SQLALCHEMY_DATABASE_URI",
        db_engine.db_uri,
    )

# Configure and run migrations unconditionally when alembic loads this file
# This is the standard alembic pattern - env.py runs at import time
configure_alembic()

if context.is_offline_mode():
    print("OFFLINE MODE")
    run_migrations_offline()
else:
    run_migrations_online()
