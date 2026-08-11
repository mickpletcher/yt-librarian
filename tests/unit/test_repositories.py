from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import (
    PlaylistRepository,
    PlaylistUpsert,
    VideoRepository,
    VideoUpsert,
)


def video_data(*, title: str = "Original", fingerprint: str = "a" * 64) -> VideoUpsert:
    return VideoUpsert(
        youtube_video_id="abc123",
        canonical_url="https://www.youtube.com/watch?v=abc123",
        title=title,
        content_fingerprint=fingerprint,
    )


def test_video_upsert_is_incremental(db_session: Session) -> None:
    repository = VideoRepository(db_session)

    created = repository.upsert(video_data())
    unchanged = repository.upsert(video_data())
    changed = repository.upsert(video_data(title="Updated", fingerprint="b" * 64))

    assert created.created is True
    assert unchanged.changed is False
    assert changed.created is False
    assert changed.changed is True
    assert repository.count() == 1
    assert changed.video.title == "Updated"


def test_playlist_membership_upsert_and_deactivation(db_session: Session) -> None:
    videos = VideoRepository(db_session)
    playlists = PlaylistRepository(db_session)
    video = videos.upsert(video_data()).video
    playlist_result = playlists.upsert(
        PlaylistUpsert(
            youtube_playlist_id="PL123",
            name="Saved videos",
            canonical_url="https://www.youtube.com/playlist?list=PL123",
            reported_video_count=1,
        )
    )

    _, created = playlists.upsert_membership(
        playlist=playlist_result.playlist, video=video, position=1
    )
    membership, created_again = playlists.upsert_membership(
        playlist=playlist_result.playlist, video=video, position=2
    )

    assert playlist_result.created is True
    assert created is True
    assert created_again is False
    assert membership.position == 2
    assert playlists.active_membership_count() == 1
    assert (
        playlists.deactivate_missing(playlist=playlist_result.playlist, observed_video_ids=set())
        == 1
    )
    assert membership.active is False
