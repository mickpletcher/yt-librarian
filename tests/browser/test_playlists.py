import pytest

from youtube_knowledge_manager.browser.playlists import (
    discovered_playlist_from_raw,
    extract_playlist_id,
    parse_reported_video_count,
)


@pytest.mark.browser
def test_extracts_playlist_id_and_reported_count() -> None:
    assert extract_playlist_id("/playlist?list=PL123&feature=share") == "PL123"
    assert extract_playlist_id(None) is None
    assert parse_reported_video_count("Updated today 1,234 videos") == 1234
    assert parse_reported_video_count("No videos") == 0
    assert parse_reported_video_count("Private playlist") is None


@pytest.mark.browser
def test_normalizes_saved_playlist_card() -> None:
    playlist = discovered_playlist_from_raw(
        {
            "href": "/playlist?list=WL",
            "title": " Watch later ",
            "metadata": "Private 42 videos",
        }
    )

    assert playlist is not None
    assert playlist.youtube_playlist_id == "WL"
    assert playlist.name == "Watch later"
    assert playlist.system_kind == "watch_later"
    assert playlist.reported_video_count == 42
