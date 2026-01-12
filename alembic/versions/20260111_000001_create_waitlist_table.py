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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # If this DB was used before migrations existed, the table may already be present.
    # Make this "initial" migration safe to run against an existing database.
    if not inspector.has_table("waitlist"):
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
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_waitlist_email ON waitlist (email)"))

    # Enforce case-insensitive uniqueness at the DB layer.
    # This prevents duplicates like Test@Email.com vs test@email.com under concurrency.
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_waitlist_email_lower ON waitlist (lower(email))"
        )
    )


def downgrade() -> None:
    op.drop_index("uq_waitlist_email_lower", table_name="waitlist")
    op.drop_index("ix_waitlist_email", table_name="waitlist")
    op.drop_table("waitlist")

