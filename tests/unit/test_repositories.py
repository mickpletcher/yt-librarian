from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import VideoRepository, VideoUpsert


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
