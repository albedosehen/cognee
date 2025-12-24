"""Initial migration

Revision ID: 8057ae7329c2
Revises:
Create Date: 2024-10-02 12:55:20.989372

"""

from typing import Sequence, Union
from datetime import datetime, timezone
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8057ae7329c2"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create base tables that the application requires.
    
    This migration is idempotent - it checks if tables exist before creating them.
    This is necessary because some deployments may have already created tables
    using Base.metadata.create_all() before migrations were properly implemented.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create principals table (base table for users and tenants via polymorphic inheritance)
    if "principals" not in existing_tables:
        op.create_table(
            "principals",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False, default=uuid4),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc)),
            sa.Column("type", sa.String(), nullable=False),
        )
        op.create_index(op.f("ix_principals_id"), "principals", ["id"], unique=False)

    # Create permissions table
    if "permissions" not in existing_tables:
        op.create_table(
            "permissions",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False, default=uuid4),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc)),
            sa.Column("name", sa.String(), nullable=False),
        )
        op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)
        op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)

    # Create tenants table (inherits from principals)
    if "tenants" not in existing_tables:
        op.create_table(
            "tenants",
            sa.Column("id", sa.UUID(), sa.ForeignKey("principals.id"), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("owner_id", sa.UUID(), nullable=True),
        )
        op.create_index(op.f("ix_tenants_name"), "tenants", ["name"], unique=True)
        op.create_index(op.f("ix_tenants_owner_id"), "tenants", ["owner_id"], unique=False)

    # Create users table (inherits from principals, uses fastapi-users structure)
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), sa.ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("hashed_password", sa.String(length=1024), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
            sa.Column("is_superuser", sa.Boolean(), nullable=False, default=False),
            sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
            sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id"), nullable=True),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)

    # Create datasets table
    if "datasets" not in existing_tables:
        op.create_table(
            "datasets",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False, default=uuid4),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc)),
            sa.Column("owner_id", sa.UUID(), nullable=True),
        )
        op.create_index(op.f("ix_datasets_owner_id"), "datasets", ["owner_id"], unique=False)

    # Create data table
    if "data" not in existing_tables:
        op.create_table(
            "data",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False, default=uuid4),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("extension", sa.String(), nullable=True),
            sa.Column("mime_type", sa.String(), nullable=True),
            sa.Column("raw_data_location", sa.String(), nullable=True),
            sa.Column("owner_id", sa.UUID(), nullable=True),
            sa.Column("content_hash", sa.String(), nullable=True),
            sa.Column("external_metadata", sa.JSON(), nullable=True),
            sa.Column("node_set", sa.JSON(), nullable=True),
            sa.Column("token_count", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc)),
        )
        op.create_index(op.f("ix_data_owner_id"), "data", ["owner_id"], unique=False)

    # Create dataset_data junction table (many-to-many between datasets and data)
    if "dataset_data" not in existing_tables:
        op.create_table(
            "dataset_data",
            sa.Column("dataset_id", sa.UUID(), sa.ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("data_id", sa.UUID(), sa.ForeignKey("data.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        )

    # Create roles table
    if "roles" not in existing_tables:
        op.create_table(
            "roles",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False, default=uuid4),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc)),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id"), nullable=True),
        )
        op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
        op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=False)

    # Create user_roles junction table
    if "user_roles" not in existing_tables:
        op.create_table(
            "user_roles",
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), primary_key=True, nullable=False),
            sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id"), primary_key=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc)),
        )

    # Create dataset_database table (stores database configuration per dataset)
    if "dataset_database" not in existing_tables:
        op.create_table(
            "dataset_database",
            sa.Column("id", sa.UUID(), primary_key=True, nullable=False, default=uuid4),
            sa.Column("dataset_id", sa.UUID(), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
            sa.Column("relational_database_url", sa.String(), nullable=True),
            sa.Column("relational_database_key", sa.String(), nullable=True),
        )
        op.create_index(op.f("ix_dataset_database_dataset_id"), "dataset_database", ["dataset_id"], unique=True)


def downgrade() -> None:
    """Remove all base tables created in upgrade.
    
    WARNING: This will delete all data. Only use in development.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop tables in reverse dependency order
    tables_to_drop = [
        "dataset_database",
        "user_roles",
        "roles",
        "dataset_data",
        "data",
        "datasets",
        "users",
        "tenants",
        "permissions",
        "principals",
    ]

    for table_name in tables_to_drop:
        if table_name in existing_tables:
            op.drop_table(table_name)
