from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from youtube_knowledge_manager.db.base import Base, TimestampMixin, utc_now


class AvailabilityStatus(StrEnum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PRIVATE = "private"
    DELETED = "deleted"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    REVIEW = "review"
    FAILED = "failed"
    SKIPPED = "skipped"


class AssignmentType(StrEnum):
    RULE = "rule"
    AI = "ai"
    MANUAL = "manual"
    IMPORTED = "imported"
    LEARNED = "learned"


class ActionStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class SyncStatus(StrEnum):
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class Video(TimestampMixin, Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    canonical_url: Mapped[str] = mapped_column(String(512))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    channel_id: Mapped[str | None] = mapped_column(String(64), index=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus, native_enum=False), default=AvailabilityStatus.UNKNOWN
    )
    privacy_status: Mapped[str | None] = mapped_column(String(32))
    liked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_discovered_at: Mapped[datetime] = mapped_column(default=utc_now)
    last_observed_at: Mapped[datetime] = mapped_column(default=utc_now, index=True)
    metadata_enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    transcript_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False), default=ProcessingStatus.PENDING
    )
    classification_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False), default=ProcessingStatus.PENDING, index=True
    )
    playlist_sync_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False), default=ProcessingStatus.PENDING
    )
    content_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    transcripts: Mapped[list[Transcript]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    category_assignments: Mapped[list[VideoCategory]] = relationship(
        back_populates="video", cascade="all, delete-orphan"
    )
    classification_runs: Mapped[list[ClassificationRun]] = relationship(back_populates="video")


class Transcript(TimestampMixin, Base):
    __tablename__ = "transcripts"
    __table_args__ = (
        UniqueConstraint("video_id", "language", "is_auto_generated"),
        Index("ix_transcripts_text_hash", "text_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    language: Mapped[str] = mapped_column(String(32))
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_text: Mapped[str | None] = mapped_column(Text)
    segment_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    retrieval_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False), default=ProcessingStatus.PENDING
    )
    retrieval_error: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    text_hash: Mapped[str | None] = mapped_column(String(64))

    video: Mapped[Video] = relationship(back_populates="transcripts")


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    youtube_playlist_name: Mapped[str | None] = mapped_column(String(255))
    youtube_playlist_id: Mapped[str | None] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    system_managed: Mapped[bool] = mapped_column(Boolean, default=False)

    parent: Mapped[Category | None] = relationship(
        remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list[Category]] = relationship(back_populates="parent")
    video_assignments: Mapped[list[VideoCategory]] = relationship(back_populates="category")


class VideoCategory(TimestampMixin, Base):
    __tablename__ = "video_categories"
    __table_args__ = (UniqueConstraint("video_id", "category_id", "assignment_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    assignment_type: Mapped[AssignmentType] = mapped_column(Enum(AssignmentType, native_enum=False))
    confidence: Mapped[float] = mapped_column(Float)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    model_or_rule_identifier: Mapped[str | None] = mapped_column(String(255))
    approved: Mapped[bool | None] = mapped_column(Boolean, default=None, index=True)

    video: Mapped[Video] = relationship(back_populates="category_assignments")
    category: Mapped[Category] = relationship(back_populates="video_assignments")


class ClassificationRun(Base):
    __tablename__ = "classification_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    raw_response: Mapped[str | None] = mapped_column(Text)
    parsed_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    token_usage: Mapped[dict[str, int] | None] = mapped_column(JSON)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    started_at: Mapped[datetime] = mapped_column(default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_information: Mapped[str | None] = mapped_column(Text)

    video: Mapped[Video] = relationship(back_populates="classification_runs")


class ClassificationRule(TimestampMixin, Base):
    __tablename__ = "classification_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rule_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus, native_enum=False), index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean)
    started_at: Mapped[datetime] = mapped_column(default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    videos_seen: Mapped[int] = mapped_column(Integer, default=0)
    videos_created: Mapped[int] = mapped_column(Integer, default=0)
    videos_changed: Mapped[int] = mapped_column(Integer, default=0)
    error_information: Mapped[str | None] = mapped_column(Text)


class BrowserAction(TimestampMixin, Base):
    __tablename__ = "browser_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_key: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    action_type: Mapped[str] = mapped_column(String(64))
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    target_playlist_id: Mapped[str | None] = mapped_column(String(128))
    target_playlist_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, native_enum=False), default=ActionStatus.PLANNED, index=True
    )
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_information: Mapped[str | None] = mapped_column(Text)

    video: Mapped[Video] = relationship()
    category: Mapped[Category | None] = relationship()
