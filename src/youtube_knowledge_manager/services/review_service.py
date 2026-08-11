from sqlalchemy import select
from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.models import (
    AssignmentType,
    ProcessingStatus,
    Video,
    VideoCategory,
)
from youtube_knowledge_manager.db.repositories import (
    CategoryRepository,
    ClassificationRepository,
    VideoRepository,
)


class ReviewService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.classifications = ClassificationRepository(session)
        self.videos = VideoRepository(session)
        self.categories = CategoryRepository(session)

    def queue(self, limit: int = 100) -> list[VideoCategory]:
        return self.classifications.list_review_queue(limit)

    def unassigned(self, limit: int = 100) -> list[Video]:
        return self.videos.list_unassigned_review(limit)

    def decide(self, assignment_id: int, *, approved: bool) -> VideoCategory:
        assignment = self.session.get(VideoCategory, assignment_id)
        if assignment is None:
            raise LookupError(f"Assignment not found: {assignment_id}")
        assignment.approved = approved
        self.session.flush()
        pending = self.session.scalar(
            select(VideoCategory.id)
            .where(
                VideoCategory.video_id == assignment.video_id,
                VideoCategory.approved.is_(None),
            )
            .limit(1)
        )
        accepted = self.session.scalar(
            select(VideoCategory.id)
            .where(
                VideoCategory.video_id == assignment.video_id,
                VideoCategory.approved.is_(True),
            )
            .limit(1)
        )
        assignment.video.classification_status = (
            ProcessingStatus.COMPLETE
            if pending is None and accepted is not None
            else ProcessingStatus.REVIEW
        )
        self.session.commit()
        return assignment

    def assign_manual(self, video_id: int, category_id: int, *, is_primary: bool) -> VideoCategory:
        video = self.videos.get(video_id)
        category = self.categories.get(category_id)
        if video is None or category is None:
            raise LookupError("Video or category not found")
        assignment = self.classifications.assign(
            video=video,
            category=category,
            assignment_type=AssignmentType.MANUAL,
            confidence=1.0,
            is_primary=is_primary,
            explanation="Approved by user in review interface",
            identifier="manual-review",
            approved=True,
        )
        video.classification_status = ProcessingStatus.COMPLETE
        self.session.commit()
        return assignment
