"""add playlist inventory

Revision ID: 6eb4836d0dc8
Revises: 0a0b1ab87743
Create Date: 2026-08-05 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6eb4836d0dc8"
down_revision: str | None = "0a0b1ab87743"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "youtube_playlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("youtube_playlist_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("canonical_url", sa.String(length=512), nullable=False),
        sa.Column("system_kind", sa.String(length=32), nullable=True),
        sa.Column("reported_video_count", sa.Integer(), nullable=True),
        sa.Column("first_discovered_at", sa.DateTime(), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_youtube_playlists")),
    )
    with op.batch_alter_table("youtube_playlists", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_youtube_playlists_last_observed_at"),
            ["last_observed_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_youtube_playlists_system_kind"), ["system_kind"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_youtube_playlists_youtube_playlist_id"),
            ["youtube_playlist_id"],
            unique=True,
        )

    op.create_table(
        "playlist_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("playlist_id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("first_discovered_at", sa.DateTime(), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["youtube_playlists.id"],
            name=op.f("fk_playlist_memberships_playlist_id_youtube_playlists"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_playlist_memberships_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_playlist_memberships")),
        sa.UniqueConstraint(
            "playlist_id",
            "video_id",
            name=op.f("uq_playlist_memberships_playlist_id"),
        ),
    )
    with op.batch_alter_table("playlist_memberships", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_playlist_memberships_active"), ["active"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_playlist_memberships_last_observed_at"),
            ["last_observed_at"],
            unique=False,
        )
        batch_op.create_index(
            "ix_playlist_memberships_playlist_active", ["playlist_id", "active"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_playlist_memberships_playlist_id"), ["playlist_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_playlist_memberships_video_id"), ["video_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("playlist_memberships", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_playlist_memberships_video_id"))
        batch_op.drop_index(batch_op.f("ix_playlist_memberships_playlist_id"))
        batch_op.drop_index("ix_playlist_memberships_playlist_active")
        batch_op.drop_index(batch_op.f("ix_playlist_memberships_last_observed_at"))
        batch_op.drop_index(batch_op.f("ix_playlist_memberships_active"))
    op.drop_table("playlist_memberships")

    with op.batch_alter_table("youtube_playlists", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_youtube_playlists_youtube_playlist_id"))
        batch_op.drop_index(batch_op.f("ix_youtube_playlists_system_kind"))
        batch_op.drop_index(batch_op.f("ix_youtube_playlists_last_observed_at"))
    op.drop_table("youtube_playlists")
