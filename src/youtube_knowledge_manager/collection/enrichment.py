import hashlib
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.session import BrowserSession
from youtube_knowledge_manager.browser.transcripts import TranscriptCollector
from youtube_knowledge_manager.browser.video_details import VideoDetailsCollector
from youtube_knowledge_manager.db.base import utc_now
from youtube_knowledge_manager.db.models import ProcessingStatus, Transcript, Video


class EnrichmentService:
    def __init__(self, session: Session, browser: BrowserSession) -> None:
        self.session = session
        self.browser = browser

    async def enrich(self, video: Video, *, include_transcript: bool = True) -> None:
        transcript = None
        if include_transcript:
            transcript = self.session.scalar(
                select(Transcript).where(
                    Transcript.video_id == video.id,
                    Transcript.language == "unknown",
                    Transcript.is_auto_generated.is_(False),
                )
            )
            if transcript is None:
                transcript = Transcript(
                    video=video,
                    language="unknown",
                    is_auto_generated=False,
                    retrieval_status=ProcessingStatus.PENDING,
                    attempts=0,
                )
                self.session.add(transcript)
            transcript.attempts += 1
            transcript.last_attempted_at = utc_now()
            transcript.retrieval_status = ProcessingStatus.IN_PROGRESS
            transcript.retrieval_error = None
            transcript.next_retry_at = None
            video.transcript_status = ProcessingStatus.IN_PROGRESS
            self.session.commit()

        try:
            details = await VideoDetailsCollector(self.browser).collect(video.canonical_url)
            video.title = details.title
            video.description = details.description
            video.channel_name = details.channel_name
            video.metadata_enriched_at = utc_now()
            if transcript is not None:
                segments = await TranscriptCollector(self.browser).collect_if_available()
                text = "\n".join(segment.text for segment in segments)
                transcript.transcript_text = text or None
                transcript.segment_json = [segment.__dict__ for segment in segments] or None
                transcript.retrieval_status = (
                    ProcessingStatus.COMPLETE if segments else ProcessingStatus.SKIPPED
                )
                transcript.retrieved_at = utc_now()
                transcript.text_hash = hashlib.sha256(text.encode()).hexdigest() if text else None
                transcript.retrieval_error = None
                transcript.next_retry_at = None
                video.transcript_status = transcript.retrieval_status
            self.session.commit()
        except Exception as exc:
            if transcript is not None:
                transcript.retrieval_status = ProcessingStatus.FAILED
                transcript.retrieval_error = str(exc)
                transcript.next_retry_at = utc_now() + timedelta(hours=24)
                video.transcript_status = ProcessingStatus.FAILED
                self.session.commit()
            raise
