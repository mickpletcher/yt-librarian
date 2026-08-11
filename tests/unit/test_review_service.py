from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.models import AssignmentType, ProcessingStatus
from youtube_knowledge_manager.db.repositories import (
    CategoryRepository,
    ClassificationRepository,
    VideoRepository,
    VideoUpsert,
)
from youtube_knowledge_manager.services.review_service import ReviewService


def test_rejected_only_proposal_returns_video_to_manual_review(db_session: Session) -> None:
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="review-video",
                canonical_url="https://www.youtube.com/watch?v=review-video",
                title="Review me",
                content_fingerprint="a" * 64,
            )
        )
        .video
    )
    category = CategoryRepository(db_session).upsert(
        name="Review",
        slug="review",
        description=None,
        youtube_playlist_name="Review",
        youtube_playlist_id="PLREVIEW",
    )
    assignment = ClassificationRepository(db_session).assign(
        video=video,
        category=category,
        assignment_type=AssignmentType.RULE,
        confidence=0.5,
        is_primary=True,
        explanation="uncertain",
        identifier="test",
        approved=None,
    )
    video.classification_status = ProcessingStatus.REVIEW
    db_session.commit()

    ReviewService(db_session).decide(assignment.id, approved=False)

    assert video.classification_status == ProcessingStatus.REVIEW
    assert [item.id for item in ReviewService(db_session).unassigned()] == [video.id]


def test_accepted_final_proposal_completes_video(db_session: Session) -> None:
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="accepted-video",
                canonical_url="https://www.youtube.com/watch?v=accepted-video",
                title="Accept me",
                content_fingerprint="b" * 64,
            )
        )
        .video
    )
    category = CategoryRepository(db_session).upsert(
        name="Accepted",
        slug="accepted",
        description=None,
        youtube_playlist_name="Accepted",
        youtube_playlist_id="PLACCEPTED",
    )
    assignment = ClassificationRepository(db_session).assign(
        video=video,
        category=category,
        assignment_type=AssignmentType.RULE,
        confidence=0.8,
        is_primary=True,
        explanation="likely",
        identifier="test",
        approved=None,
    )
    video.classification_status = ProcessingStatus.REVIEW
    db_session.commit()

    ReviewService(db_session).decide(assignment.id, approved=True)

    assert video.classification_status == ProcessingStatus.COMPLETE
