from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import VideoRepository
from youtube_knowledge_manager.search.summaries import create_local_summary


@dataclass(frozen=True)
class SearchResult:
    video_id: int
    youtube_video_id: str
    title: str
    channel_name: str | None
    canonical_url: str
    summary: str | None


class TextSearchService:
    def __init__(self, session: Session) -> None:
        self.videos = VideoRepository(session)

    def search(
        self, query: str = "", category_slug: str | None = None, limit: int = 100
    ) -> list[SearchResult]:
        return [
            SearchResult(
                video_id=video.id,
                youtube_video_id=video.youtube_video_id,
                title=video.title,
                channel_name=video.channel_name,
                canonical_url=video.canonical_url,
                summary=create_local_summary(video),
            )
            for video in self.videos.search(query=query, category_slug=category_slug, limit=limit)
        ]
