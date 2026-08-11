from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import youtube_knowledge_manager.collection.enrichment as enrichment
from youtube_knowledge_manager.browser.transcripts import TranscriptSegment
from youtube_knowledge_manager.browser.video_details import VideoDetails
from youtube_knowledge_manager.collection.enrichment import EnrichmentService
from youtube_knowledge_manager.db.models import ProcessingStatus, Transcript
from youtube_knowledge_manager.db.repositories import VideoRepository, VideoUpsert


def _video(db_session: Session):  # type: ignore[no-untyped-def]
    return (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="enrich-video",
                canonical_url="https://www.youtube.com/watch?v=enrich-video",
                title="Before",
                content_fingerprint="a" * 64,
            )
        )
        .video
    )


@pytest.mark.asyncio
async def test_transcript_enrichment_is_idempotent(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    video = _video(db_session)

    class DetailsCollector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self, _: str) -> VideoDetails:
            return VideoDetails(title="After", description="Description", channel_name="Channel")

    class TranscriptCollector:
        calls = 0

        def __init__(self, _: object) -> None:
            pass

        async def collect_if_available(self) -> list[TranscriptSegment]:
            self.__class__.calls += 1
            return [TranscriptSegment(timestamp="0:00", text=f"Text {self.calls}")]

    monkeypatch.setattr(enrichment, "VideoDetailsCollector", DetailsCollector)
    monkeypatch.setattr(enrichment, "TranscriptCollector", TranscriptCollector)
    service = EnrichmentService(db_session, MagicMock())

    await service.enrich(video)
    await service.enrich(video)

    transcripts = list(db_session.scalars(select(Transcript)))
    assert len(transcripts) == 1
    assert transcripts[0].attempts == 2
    assert transcripts[0].transcript_text == "Text 2"
    assert transcripts[0].retrieval_status == ProcessingStatus.COMPLETE
    assert transcripts[0].retrieval_error is None


@pytest.mark.asyncio
async def test_failed_transcript_attempt_records_retry_state(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    video = _video(db_session)

    class DetailsCollector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self, _: str) -> VideoDetails:
            raise RuntimeError("transient failure")

    monkeypatch.setattr(enrichment, "VideoDetailsCollector", DetailsCollector)

    with pytest.raises(RuntimeError, match="transient failure"):
        await EnrichmentService(db_session, MagicMock()).enrich(video)

    transcript = db_session.scalar(select(Transcript))
    assert transcript is not None
    assert transcript.attempts == 1
    assert transcript.retrieval_status == ProcessingStatus.FAILED
    assert transcript.next_retry_at is not None
    assert video.transcript_status == ProcessingStatus.FAILED
