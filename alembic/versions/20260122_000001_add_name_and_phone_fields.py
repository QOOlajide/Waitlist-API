"""Add first_name, last_name, and phone fields to waitlist.

Revision ID: 20260122_000001
Revises: 20260111_000001
Create Date: 2026-01-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260122_000001"
down_revision = "20260111_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns (nullable first for existing rows)
    op.add_column("waitlist", sa.Column("first_name", sa.String(50), nullable=True))
    op.add_column("waitlist", sa.Column("last_name", sa.String(50), nullable=True))
    op.add_column("waitlist", sa.Column("phone", sa.String(20), nullable=True))
    
    # Set default values for any existing rows
    op.execute(
        sa.text("UPDATE waitlist SET first_name = 'Unknown' WHERE first_name IS NULL")
    )
    op.execute(
        sa.text("UPDATE waitlist SET last_name = 'Unknown' WHERE last_name IS NULL")
    )
    op.execute(
        sa.text("UPDATE waitlist SET phone = '+2340000000000' WHERE phone IS NULL")
    )
    
    # Now make columns non-nullable
    op.alter_column("waitlist", "first_name", nullable=False)
    op.alter_column("waitlist", "last_name", nullable=False)
    op.alter_column("waitlist", "phone", nullable=False)
    
    # Add unique constraint on phone
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_waitlist_phone ON waitlist (phone)"
        )
    )
    
    # Add unique constraint on email (not just case-insensitive index)
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_waitlist_email ON waitlist (email)"
        )
    )
    
    # Index for phone lookups
    op.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_waitlist_phone ON waitlist (phone)")
    )


def downgrade() -> None:
    op.drop_index("ix_waitlist_phone", table_name="waitlist")
    op.drop_index("uq_waitlist_phone", table_name="waitlist")
    op.drop_index("uq_waitlist_email", table_name="waitlist")
    op.drop_column("waitlist", "phone")
    op.drop_column("waitlist", "last_name")
    op.drop_column("waitlist", "first_name")
