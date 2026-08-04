from youtube_knowledge_manager.browser.liked_videos import CollectedVideo
from youtube_knowledge_manager.collection.crawler import (
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
