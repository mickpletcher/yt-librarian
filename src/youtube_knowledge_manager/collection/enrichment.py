import hashlib

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
        details = await VideoDetailsCollector(self.browser).collect(video.canonical_url)
        video.title = details.title
        video.description = details.description
        video.channel_name = details.channel_name
        video.metadata_enriched_at = utc_now()
        if include_transcript:
            segments = await TranscriptCollector(self.browser).collect_if_available()
            text = "\n".join(segment.text for segment in segments)
            transcript = Transcript(
                video=video,
                language="unknown",
                is_auto_generated=False,
                transcript_text=text or None,
                segment_json=[segment.__dict__ for segment in segments] or None,
                retrieval_status=(
                    ProcessingStatus.COMPLETE if segments else ProcessingStatus.SKIPPED
                ),
                retrieved_at=utc_now(),
                text_hash=hashlib.sha256(text.encode()).hexdigest() if text else None,
            )
            self.session.add(transcript)
            video.transcript_status = transcript.retrieval_status
        self.session.commit()
