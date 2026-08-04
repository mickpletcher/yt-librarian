from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from youtube_knowledge_manager.db.base import utc_now
from youtube_knowledge_manager.db.models import (
    ActionStatus,
    AssignmentType,
    BrowserAction,
    Category,
    ClassificationRun,
    ProcessingStatus,
    SyncRun,
    SyncStatus,
    Video,
    VideoCategory,
)


@dataclass(frozen=True)
class VideoUpsert:
    youtube_video_id: str
    canonical_url: str
    title: str
    content_fingerprint: str
    description: str | None = None
    channel_id: str | None = None
    channel_name: str | None = None
    published_at: datetime | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    privacy_status: str | None = None
    liked_at: datetime | None = None
    raw_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class UpsertResult:
    video: Video
    created: bool
    changed: bool


class VideoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, video_id: int) -> Video | None:
        return self.session.get(Video, video_id)

    def get_by_youtube_id(self, youtube_video_id: str) -> Video | None:
        return self.session.scalar(select(Video).where(Video.youtube_video_id == youtube_video_id))

    def upsert(self, data: VideoUpsert) -> UpsertResult:
        now = utc_now()
        video = self.get_by_youtube_id(data.youtube_video_id)
        if video is None:
            video = Video(
                youtube_video_id=data.youtube_video_id,
                canonical_url=data.canonical_url,
                title=data.title,
                description=data.description,
                channel_id=data.channel_id,
                channel_name=data.channel_name,
                published_at=data.published_at,
                duration_seconds=data.duration_seconds,
                thumbnail_url=data.thumbnail_url,
                privacy_status=data.privacy_status,
                liked_at=data.liked_at,
                content_fingerprint=data.content_fingerprint,
                raw_metadata=data.raw_metadata or {},
                first_discovered_at=now,
                last_observed_at=now,
            )
            self.session.add(video)
            self.session.flush()
            return UpsertResult(video=video, created=True, changed=True)

        changed = video.content_fingerprint != data.content_fingerprint
        video.last_observed_at = now
        if changed:
            video.canonical_url = data.canonical_url
            video.title = data.title
            video.description = data.description
            video.channel_id = data.channel_id
            video.channel_name = data.channel_name
            video.published_at = data.published_at
            video.duration_seconds = data.duration_seconds
            video.thumbnail_url = data.thumbnail_url
            video.privacy_status = data.privacy_status
            video.liked_at = data.liked_at
            video.content_fingerprint = data.content_fingerprint
            video.raw_metadata = data.raw_metadata or {}
            video.classification_status = ProcessingStatus.PENDING
        self.session.flush()
        return UpsertResult(video=video, created=False, changed=changed)

    def list_for_classification(self, limit: int = 100) -> list[Video]:
        return list(
            self.session.scalars(
                select(Video)
                .where(Video.classification_status == ProcessingStatus.PENDING)
                .order_by(Video.first_discovered_at)
                .limit(limit)
            )
        )

    def list_recent(self, limit: int = 100) -> list[Video]:
        return list(
            self.session.scalars(select(Video).order_by(Video.last_observed_at.desc()).limit(limit))
        )

    def list_unassigned_review(self, limit: int = 100) -> list[Video]:
        return list(
            self.session.scalars(
                select(Video)
                .where(
                    Video.classification_status == ProcessingStatus.REVIEW,
                    ~Video.category_assignments.any(VideoCategory.approved.is_(None)),
                )
                .order_by(Video.last_observed_at.desc())
                .limit(limit)
            )
        )

    def count(self) -> int:
        return self.session.scalar(select(func.count(Video.id))) or 0

    def search(
        self,
        query: str = "",
        category_slug: str | None = None,
        limit: int = 100,
    ) -> list[Video]:
        statement: Select[tuple[Video]] = select(Video).distinct()
        if query.strip():
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Video.title.ilike(pattern),
                    Video.description.ilike(pattern),
                    Video.channel_name.ilike(pattern),
                )
            )
        if category_slug:
            statement = (
                statement.join(VideoCategory)
                .join(Category)
                .where(Category.slug == category_slug, VideoCategory.approved.is_(True))
            )
        statement = statement.order_by(Video.last_observed_at.desc()).limit(limit)
        return list(self.session.scalars(statement))


class CategoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def get_by_slug(self, slug: str) -> Category | None:
        return self.session.scalar(select(Category).where(Category.slug == slug))

    def list_enabled(self) -> list[Category]:
        return list(
            self.session.scalars(
                select(Category).where(Category.enabled.is_(True)).order_by(Category.name)
            )
        )

    def upsert(
        self,
        *,
        name: str,
        slug: str,
        description: str | None,
        youtube_playlist_name: str | None,
        youtube_playlist_id: str | None = None,
        parent_id: int | None = None,
        enabled: bool = True,
        system_managed: bool = False,
    ) -> Category:
        category = self.get_by_slug(slug)
        if category is None:
            category = Category(name=name, slug=slug)
            self.session.add(category)
        category.name = name
        category.description = description
        category.youtube_playlist_name = youtube_playlist_name
        category.youtube_playlist_id = youtube_playlist_id
        category.parent_id = parent_id
        category.enabled = enabled
        category.system_managed = system_managed
        self.session.flush()
        return category


class ClassificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def assign(
        self,
        *,
        video: Video,
        category: Category,
        assignment_type: AssignmentType,
        confidence: float,
        is_primary: bool,
        explanation: str,
        identifier: str,
        approved: bool | None,
    ) -> VideoCategory:
        assignment = self.session.scalar(
            select(VideoCategory).where(
                VideoCategory.video_id == video.id,
                VideoCategory.category_id == category.id,
                VideoCategory.assignment_type == assignment_type,
            )
        )
        if assignment is None:
            assignment = VideoCategory(
                video=video,
                category=category,
                assignment_type=assignment_type,
                confidence=confidence,
            )
            self.session.add(assignment)
        assignment.confidence = confidence
        assignment.is_primary = is_primary
        assignment.explanation = explanation
        assignment.model_or_rule_identifier = identifier
        assignment.approved = approved
        self.session.flush()
        return assignment

    def list_review_queue(self, limit: int = 100) -> list[VideoCategory]:
        return list(
            self.session.scalars(
                select(VideoCategory)
                .options(joinedload(VideoCategory.video), joinedload(VideoCategory.category))
                .where(VideoCategory.approved.is_(None))
                .order_by(VideoCategory.confidence.desc())
                .limit(limit)
            )
        )

    def list_approved(self, limit: int = 1000) -> list[VideoCategory]:
        return list(
            self.session.scalars(
                select(VideoCategory)
                .options(joinedload(VideoCategory.video), joinedload(VideoCategory.category))
                .where(VideoCategory.approved.is_(True))
                .order_by(VideoCategory.created_at)
                .limit(limit)
            )
        )

    def add_run(self, run: ClassificationRun) -> ClassificationRun:
        self.session.add(run)
        self.session.flush()
        return run


class SyncRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def start(self, dry_run: bool) -> SyncRun:
        run = SyncRun(status=SyncStatus.RUNNING, dry_run=dry_run)
        self.session.add(run)
        self.session.flush()
        return run

    def finish(self, run: SyncRun, *, failed: bool = False, error: str | None = None) -> None:
        run.completed_at = utc_now()
        run.status = (
            SyncStatus.FAILED
            if failed
            else (SyncStatus.DRY_RUN if run.dry_run else SyncStatus.COMPLETE)
        )
        run.error_information = error
        self.session.flush()

    def latest(self) -> SyncRun | None:
        return self.session.scalar(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1))


class BrowserActionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_add(
        self, *, video: Video, category: Category, dry_run: bool
    ) -> tuple[BrowserAction, bool]:
        target = category.youtube_playlist_id or category.youtube_playlist_name
        if target is None:
            raise ValueError(f"Category {category.slug} has no YouTube playlist mapping")
        action_key = f"playlist-add:{video.youtube_video_id}:{target}"
        action = self.session.scalar(
            select(BrowserAction).where(BrowserAction.action_key == action_key)
        )
        if action is not None:
            return action, False
        action = BrowserAction(
            action_key=action_key,
            action_type="playlist_add",
            video_id=video.id,
            category_id=category.id,
            target_playlist_id=category.youtube_playlist_id,
            target_playlist_name=category.youtube_playlist_name or category.name,
            dry_run=dry_run,
            status=ActionStatus.PLANNED,
        )
        self.session.add(action)
        self.session.flush()
        return action, True

    def list_pending(self, limit: int = 100) -> list[BrowserAction]:
        return list(
            self.session.scalars(
                select(BrowserAction)
                .options(joinedload(BrowserAction.video), joinedload(BrowserAction.category))
                .where(BrowserAction.status.in_([ActionStatus.PLANNED, ActionStatus.FAILED]))
                .order_by(BrowserAction.created_at)
                .limit(limit)
            )
        )

    def list_recent(self, limit: int = 100) -> list[BrowserAction]:
        return list(
            self.session.scalars(
                select(BrowserAction)
                .options(joinedload(BrowserAction.video), joinedload(BrowserAction.category))
                .order_by(BrowserAction.created_at.desc())
                .limit(limit)
            )
        )
