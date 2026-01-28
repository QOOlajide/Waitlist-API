"""Create contact_messages table.

Revision ID: 20260128_000001
Revises: 20260122_000001
Create Date: 2026-01-28
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260128_000001"
down_revision = "20260122_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Create table if it doesn't exist
    if not inspector.has_table("contact_messages"):
        op.create_table(
            "contact_messages",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("subject", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("is_spam", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # Index for rate limiting by IP
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_contact_messages_ip_address "
            "ON contact_messages (ip_address)"
        )
    )
    
    # Index for rate limiting by email
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_contact_messages_email "
            "ON contact_messages (email)"
        )
    )
    
    # Index for filtering by timestamp (used in rate limit queries)
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_contact_messages_created_at "
            "ON contact_messages (created_at)"
        )
    )
    
    # Composite index for efficient rate limit queries
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_contact_messages_ip_created "
            "ON contact_messages (ip_address, created_at)"
        )
    )
    
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_contact_messages_email_created "
            "ON contact_messages (lower(email), created_at)"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_contact_messages_email_created", table_name="contact_messages")
    op.drop_index("ix_contact_messages_ip_created", table_name="contact_messages")
    op.drop_index("ix_contact_messages_created_at", table_name="contact_messages")
    op.drop_index("ix_contact_messages_email", table_name="contact_messages")
    op.drop_index("ix_contact_messages_ip_address", table_name="contact_messages")
    op.drop_table("contact_messages")
