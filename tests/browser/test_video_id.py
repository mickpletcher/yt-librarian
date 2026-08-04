import pytest

from youtube_knowledge_manager.browser.liked_videos import extract_video_id


@pytest.mark.browser
def test_extracts_video_id_from_youtube_urls() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=abc123&list=LL") == "abc123"
    assert extract_video_id("https://youtu.be/xyz987") == "xyz987"
    assert extract_video_id(None) is None
