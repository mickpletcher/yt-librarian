import pytest

from youtube_knowledge_manager.browser.liked_videos import (
    collected_video_from_raw_item,
    extract_video_id,
    video_href_matches_playlist,
)


@pytest.mark.browser
def test_extracts_video_id_from_youtube_urls() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=abc123&list=LL") == "abc123"
    assert extract_video_id("https://youtu.be/xyz987") == "xyz987"
    assert extract_video_id("https://www.youtube.com/shorts/short123") == "short123"
    assert extract_video_id("/live/live123") == "live123"
    assert extract_video_id(None) is None


@pytest.mark.browser
def test_video_href_must_match_active_playlist() -> None:
    assert video_href_matches_playlist("/watch?v=abc&list=PL123&index=2", "PL123")
    assert not video_href_matches_playlist("/watch?v=abc", "PL123")
    assert not video_href_matches_playlist("/watch?v=abc&list=OTHER", "PL123")


@pytest.mark.browser
def test_normalizes_current_lockup_item() -> None:
    video = collected_video_from_raw_item(
        {
            "href": "/shorts/short123?list=LL",
            "title": "  Example short  ",
            "channel_name": "Example channel",
            "channel_href": "/@example",
            "thumbnail": "https://example.test/image.jpg",
            "duration": " 1:23 ",
        },
        17,
    )

    assert video is not None
    assert video.youtube_video_id == "short123"
    assert video.title == "Example short"
    assert video.channel_id == "@example"
    assert video.duration_text == "1:23"
    assert video.position == 17
