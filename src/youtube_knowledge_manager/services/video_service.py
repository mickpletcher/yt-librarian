from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.models import Video
from youtube_knowledge_manager.db.repositories import (
    BrowserActionRepository,
    ClassificationRepository,
    SyncRunRepository,
    VideoRepository,
)


@dataclass(frozen=True)
class DashboardSummary:
    total_videos: int
    review_items: int
    pending_actions: int
    last_sync_status: str | None


class VideoService:
    def __init__(self, session: Session) -> None:
        self.videos = VideoRepository(session)
        self.classifications = ClassificationRepository(session)
        self.actions = BrowserActionRepository(session)
        self.sync_runs = SyncRunRepository(session)

    def recent(self, limit: int = 100) -> list[Video]:
        return self.videos.list_recent(limit)

    def dashboard(self) -> DashboardSummary:
        latest = self.sync_runs.latest()
        return DashboardSummary(
            total_videos=self.videos.count(),
            review_items=len(self.classifications.list_review_queue(limit=10_000)),
            pending_actions=len(self.actions.list_pending(limit=10_000)),
            last_sync_status=latest.status.value if latest else None,
        )
