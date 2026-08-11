from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import VideoRepository, VideoUpsert
from youtube_knowledge_manager.services.privacy_inventory import collect_privacy_inventory


def test_privacy_inventory_contains_counts_only(db_session: Session) -> None:
    VideoRepository(db_session).upsert(
        VideoUpsert(
            youtube_video_id="private-id",
            canonical_url="https://www.youtube.com/watch?v=private-id",
            title="Private title",
            content_fingerprint="f" * 64,
        )
    )
    db_session.commit()

    payload = collect_privacy_inventory(db_session).sanitized_payload()
    serialized = str(payload)

    assert payload["schema_version"] == 1
    assert payload["counts"]["videos"] == 1  # type: ignore[index]
    assert "private-id" not in serialized
    assert "Private title" not in serialized
    assert "youtube.com" not in serialized
