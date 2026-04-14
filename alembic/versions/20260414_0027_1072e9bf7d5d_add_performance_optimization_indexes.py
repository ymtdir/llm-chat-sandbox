"""Add performance optimization indexes

Revision ID: 1072e9bf7d5d
Revises: 24cda6b169f3
Create Date: 2026-04-14 00:27:59.908055

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1072e9bf7d5d'
down_revision: str | Sequence[str] | None = '24cda6b169f3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance optimization indexes."""
    # Composite indexes for messages table
    op.create_index(
        "idx_messages_conversation_sent", "messages", ["conversation_id", "sent_at"]
    )

    # Partial index for pending scheduled responses
    op.create_index(
        "idx_scheduled_responses_pending",
        "scheduled_responses",
        ["status", "scheduled_at"],
        postgresql_where=sa.text("status = 'PENDING'"),
    )

    # Composite index for diaries
    op.create_index("idx_diaries_user_date", "diaries", ["user_id", "diary_date"])


def downgrade() -> None:
    """Drop performance optimization indexes."""
    op.drop_index("idx_diaries_user_date", table_name="diaries")
    op.drop_index("idx_scheduled_responses_pending", table_name="scheduled_responses")
    op.drop_index("idx_messages_conversation_sent", table_name="messages")
