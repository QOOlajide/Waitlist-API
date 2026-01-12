"""Create waitlist table (case-insensitive unique email).

Revision ID: 20260111_000001
Revises: 
Create Date: 2026-01-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260111_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Helpful index for lookups / admin export.
    op.create_index("ix_waitlist_email", "waitlist", ["email"], unique=False)

    # Enforce case-insensitive uniqueness at the DB layer.
    # This prevents duplicates like Test@Email.com vs test@email.com under concurrency.
    op.create_index(
        "uq_waitlist_email_lower",
        "waitlist",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_waitlist_email_lower", table_name="waitlist")
    op.drop_index("ix_waitlist_email", table_name="waitlist")
    op.drop_table("waitlist")

