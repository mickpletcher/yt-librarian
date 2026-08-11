from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.models import (
    BrowserAction,
    Category,
    ClassificationRun,
    PlaylistMembership,
    SyncRun,
    Transcript,
    Video,
    VideoCategory,
    YouTubePlaylist,
)


@dataclass(frozen=True)
class PrivacyInventory:
    videos: int
    playlists: int
    playlist_memberships: int
    transcripts: int
    categories: int
    category_assignments: int
    classification_runs: int
    synchronization_runs: int
    browser_actions: int

    def sanitized_payload(self) -> dict[str, object]:
        return {"schema_version": 1, "counts": asdict(self)}


def collect_privacy_inventory(session: Session) -> PrivacyInventory:
    def count(model: type[object]) -> int:
        return int(session.scalar(select(func.count()).select_from(model)) or 0)

    return PrivacyInventory(
        videos=count(Video),
        playlists=count(YouTubePlaylist),
        playlist_memberships=count(PlaylistMembership),
        transcripts=count(Transcript),
        categories=count(Category),
        category_assignments=count(VideoCategory),
        classification_runs=count(ClassificationRun),
        synchronization_runs=count(SyncRun),
        browser_actions=count(BrowserAction),
    )
