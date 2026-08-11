"""add sync operation

Revision ID: d5a2490be372
Revises: c4d8f1279a61
Create Date: 2026-08-11 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5a2490be372"
down_revision: str | None = "c4d8f1279a61"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "operation",
                sa.String(length=64),
                nullable=False,
                server_default="liked_videos",
            )
        )
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.alter_column("operation", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.drop_column("operation")
