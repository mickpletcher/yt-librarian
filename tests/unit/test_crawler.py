import pytest
from sqlalchemy.orm import Session

import youtube_knowledge_manager.collection.crawler as crawler_module
from youtube_knowledge_manager.browser.liked_videos import (
    CollectedVideo,
    PlaylistCrawlResult,
)
from youtube_knowledge_manager.collection.crawler import (
    Crawler,
    IncompletePlaylistCrawlError,
    content_fingerprint,
    parse_duration_seconds,
)


def test_parse_duration() -> None:
    assert parse_duration_seconds("12:34") == 754
    assert parse_duration_seconds("1:02:03") == 3723
    assert parse_duration_seconds("LIVE") is None


def test_fingerprint_ignores_playlist_position() -> None:
    first = CollectedVideo(
        youtube_video_id="abc123",
        canonical_url="https://www.youtube.com/watch?v=abc123",
        title="Title",
        position=1,
    )
    later = CollectedVideo(
        youtube_video_id="abc123",
        canonical_url="https://www.youtube.com/watch?v=abc123",
        title="Title",
        position=99,
    )
    assert content_fingerprint(first) == content_fingerprint(later)


@pytest.mark.asyncio
async def test_crawler_rejects_incomplete_liked_videos_run(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Collector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self, **_: object) -> PlaylistCrawlResult:
            return PlaylistCrawlResult(
                videos=[],
                complete=False,
                termination_reason="reported_count_mismatch",
            )

    monkeypatch.setattr(crawler_module, "LikedVideosCollector", Collector)

    with pytest.raises(IncompletePlaylistCrawlError, match="stopped incomplete"):
        await Crawler(db_session, dry_run=True).run(object())  # type: ignore[arg-type]
