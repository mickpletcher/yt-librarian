from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import VideoRepository, VideoUpsert
from youtube_knowledge_manager.search.text_search import TextSearchService


def test_text_search_finds_title(db_session: Session) -> None:
    VideoRepository(db_session).upsert(
        VideoUpsert(
            youtube_video_id="abc",
            canonical_url="https://www.youtube.com/watch?v=abc",
            title="PowerShell automation",
            description="A practical guide to automation with PowerShell across managed endpoints.",
            channel_name="Engineering",
            content_fingerprint="a" * 64,
        )
    )
    db_session.commit()

    results = TextSearchService(db_session).search("powershell")

    assert len(results) == 1
    assert results[0].youtube_video_id == "abc"
    assert results[0].summary == (
        "A practical guide to automation with PowerShell across managed endpoints."
    )
