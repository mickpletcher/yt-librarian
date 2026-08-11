"""add transcript retry state

Revision ID: c4d8f1279a61
Revises: 6eb4836d0dc8
Create Date: 2026-08-11 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4d8f1279a61"
down_revision: str | None = "6eb4836d0dc8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("transcripts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(
            sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table("transcripts", schema=None) as batch_op:
        batch_op.alter_column("attempts", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("transcripts", schema=None) as batch_op:
        batch_op.drop_column("next_retry_at")
        batch_op.drop_column("last_attempted_at")
        batch_op.drop_column("attempts")
