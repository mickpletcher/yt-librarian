from sqlalchemy.orm import Session

from youtube_knowledge_manager.classification.classifier import ClassificationEngine
from youtube_knowledge_manager.classification.schemas import ClassificationInput
from youtube_knowledge_manager.db.models import (
    AssignmentType,
    ClassificationRun,
    ProcessingStatus,
)
from youtube_knowledge_manager.db.repositories import (
    CategoryRepository,
    ClassificationRepository,
    VideoRepository,
)
from youtube_knowledge_manager.settings import Settings


class ClassificationService:
    def __init__(self, settings: Settings, session: Session, engine: ClassificationEngine) -> None:
        self.settings = settings
        self.session = session
        self.engine = engine
        self.videos = VideoRepository(session)
        self.categories = CategoryRepository(session)
        self.classifications = ClassificationRepository(session)

    def classify_pending(self, *, limit: int = 100, write: bool = False) -> int:
        processed = 0
        for video in self.videos.list_for_classification(limit=limit):
            transcript = video.transcripts[0].transcript_text if video.transcripts else None
            outcome = self.engine.classify(
                ClassificationInput(
                    youtube_video_id=video.youtube_video_id,
                    title=video.title,
                    description=video.description,
                    channel_name=video.channel_name,
                    transcript_text=transcript,
                )
            )
            if not write:
                processed += 1
                continue
            assignment_type = (
                AssignmentType.RULE if outcome.provider == "rules" else AssignmentType.AI
            )
            for decision in outcome.decisions:
                category = self.categories.get_by_slug(decision.category_slug)
                if category is None:
                    continue
                approved = (
                    True
                    if decision.confidence >= self.settings.review_confidence_threshold
                    else None
                )
                self.classifications.assign(
                    video=video,
                    category=category,
                    assignment_type=assignment_type,
                    confidence=decision.confidence,
                    is_primary=decision.is_primary,
                    explanation=decision.explanation,
                    identifier=decision.identifier,
                    approved=approved,
                )
            if outcome.provider not in {"rules", "none"}:
                self.classifications.add_run(
                    ClassificationRun(
                        video_id=video.id,
                        provider=outcome.provider,
                        model=outcome.model or "unknown",
                        prompt_version=self.settings.ai_prompt_version,
                        input_hash=outcome.input_hash,
                        raw_response=outcome.raw_response,
                        parsed_result={
                            "decisions": [decision.model_dump() for decision in outcome.decisions]
                        },
                        token_usage=outcome.token_usage,
                        started_at=outcome.started_at or outcome.completed_at,
                        completed_at=outcome.completed_at,
                        error_information=outcome.error,
                    )
                )
            needs_review = not outcome.decisions or any(
                decision.confidence < self.settings.review_confidence_threshold
                for decision in outcome.decisions
            )
            video.classification_status = (
                ProcessingStatus.REVIEW if needs_review else ProcessingStatus.COMPLETE
            )
            self.session.commit()
            processed += 1
        return processed
