import hashlib
import json
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.liked_videos import CollectedVideo, LikedVideosCollector
from youtube_knowledge_manager.browser.session import BrowserSession
from youtube_knowledge_manager.db.repositories import VideoRepository, VideoUpsert


@dataclass
class CrawlSummary:
    seen: int = 0
    created: int = 0
    changed: int = 0


def parse_duration_seconds(value: str | None) -> int | None:
    if not value:
        return None
    parts = value.strip().split(":")
    if not all(re.fullmatch(r"\d+", part) for part in parts) or len(parts) not in {2, 3}:
        return None
    values = [int(part) for part in parts]
    if len(values) == 2:
        return values[0] * 60 + values[1]
    return values[0] * 3600 + values[1] * 60 + values[2]


def content_fingerprint(video: CollectedVideo) -> str:
    payload = {
        "id": video.youtube_video_id,
        "title": video.title,
        "channel_id": video.channel_id,
        "channel_name": video.channel_name,
        "thumbnail_url": video.thumbnail_url,
        "duration": video.duration_text,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class Crawler:
    def __init__(self, session: Session, *, dry_run: bool) -> None:
        self.session = session
        self.dry_run = dry_run
        self.repository = VideoRepository(session)

    async def run(self, browser: BrowserSession) -> CrawlSummary:
        summary = CrawlSummary()

        async def persist(video: CollectedVideo) -> None:
            summary.seen += 1
            if self.dry_run:
                return
            result = self.repository.upsert(
                VideoUpsert(
                    youtube_video_id=video.youtube_video_id,
                    canonical_url=video.canonical_url,
                    title=video.title,
                    channel_id=video.channel_id,
                    channel_name=video.channel_name,
                    duration_seconds=parse_duration_seconds(video.duration_text),
                    thumbnail_url=video.thumbnail_url,
                    content_fingerprint=content_fingerprint(video),
                    raw_metadata=video.raw_metadata,
                )
            )
            summary.created += int(result.created)
            summary.changed += int(result.changed and not result.created)
            self.session.commit()

        await LikedVideosCollector(browser).collect(on_video=persist)
        return summary
