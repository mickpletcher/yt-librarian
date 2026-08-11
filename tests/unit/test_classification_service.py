from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from youtube_knowledge_manager.classification.classifier import ClassificationOutcome
from youtube_knowledge_manager.classification.schemas import ClassificationDecision
from youtube_knowledge_manager.db.models import ClassificationRun, ProcessingStatus
from youtube_knowledge_manager.db.repositories import (
    CategoryRepository,
    VideoRepository,
    VideoUpsert,
)
from youtube_knowledge_manager.services.classification_service import ClassificationService
from youtube_knowledge_manager.settings import Settings


def _pending_video(db_session: Session, youtube_id: str):  # type: ignore[no-untyped-def]
    return (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id=youtube_id,
                canonical_url=f"https://www.youtube.com/watch?v={youtube_id}",
                title="Classify",
                content_fingerprint="d" * 64,
            )
        )
        .video
    )


def test_classification_records_token_cost(db_session: Session) -> None:
    video = _pending_video(db_session, "cost-video")
    CategoryRepository(db_session).upsert(
        name="Cost",
        slug="cost",
        description=None,
        youtube_playlist_name="Cost",
        youtube_playlist_id="PLCOST",
    )
    db_session.commit()

    class Engine:
        def classify(self, *_: object, **__: object) -> ClassificationOutcome:
            return ClassificationOutcome(
                decisions=[
                    ClassificationDecision(
                        category_slug="cost",
                        confidence=0.9,
                        is_primary=True,
                        explanation="match",
                        identifier="fake",
                    )
                ],
                provider="fake",
                model="fake-model",
                input_hash="e" * 64,
                token_usage={"input_tokens": 1000, "output_tokens": 500, "total_tokens": 1500},
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )

    settings = Settings(
        ai_input_cost_per_million=2.0,
        ai_output_cost_per_million=4.0,
    )
    ClassificationService(settings, db_session, Engine()).classify_pending(  # type: ignore[arg-type]
        write=True
    )

    run = db_session.scalar(select(ClassificationRun))
    assert run is not None
    assert run.estimated_cost == Decimal("0.004000")
    assert video.classification_status == ProcessingStatus.COMPLETE


def test_daily_token_limit_disables_more_ai_calls(db_session: Session) -> None:
    video = _pending_video(db_session, "budget-video")
    db_session.add(
        ClassificationRun(
            video_id=video.id,
            provider="fake",
            model="fake",
            prompt_version="v1",
            input_hash="f" * 64,
            token_usage={"total_tokens": 100},
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
    )
    db_session.commit()
    observed: list[bool] = []

    class Engine:
        def classify(self, *_: object, allow_ai: bool = True) -> ClassificationOutcome:
            observed.append(allow_ai)
            return ClassificationOutcome(
                decisions=[],
                provider="budget",
                input_hash="0" * 64,
                completed_at=datetime.now(UTC),
                error="Daily AI token limit reached",
            )

    ClassificationService(
        Settings(ai_daily_token_limit=100),
        db_session,
        Engine(),  # type: ignore[arg-type]
    ).classify_pending(write=True)

    assert observed == [False]
    assert video.classification_status == ProcessingStatus.REVIEW


def test_zero_daily_token_limit_disables_ai_calls(db_session: Session) -> None:
    _pending_video(db_session, "disabled-budget-video")
    db_session.commit()
    observed: list[bool] = []

    class Engine:
        def classify(self, *_: object, allow_ai: bool = True) -> ClassificationOutcome:
            observed.append(allow_ai)
            return ClassificationOutcome(
                decisions=[],
                provider="none",
                input_hash="1" * 64,
                completed_at=datetime.now(UTC),
            )

    ClassificationService(
        Settings(ai_daily_token_limit=0),
        db_session,
        Engine(),  # type: ignore[arg-type]
    ).classify_pending(write=True)

    assert observed == [False]


def test_preview_classification_never_calls_ai(db_session: Session) -> None:
    video = _pending_video(db_session, "preview-video")
    db_session.commit()
    observed: list[bool] = []

    class Engine:
        def classify(self, *_: object, allow_ai: bool = True) -> ClassificationOutcome:
            observed.append(allow_ai)
            return ClassificationOutcome(
                decisions=[],
                provider="none",
                input_hash="2" * 64,
                completed_at=datetime.now(UTC),
            )

    ClassificationService(
        Settings(ai_daily_token_limit=100),
        db_session,
        Engine(),  # type: ignore[arg-type]
    ).classify_pending(write=False)

    assert observed == [False]
    assert video.classification_status == ProcessingStatus.PENDING
    assert db_session.scalar(select(ClassificationRun)) is None
