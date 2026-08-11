from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.models import AssignmentType
from youtube_knowledge_manager.db.repositories import (
    CategoryRepository,
    ClassificationRepository,
    PlaylistRepository,
    PlaylistUpsert,
    VideoRepository,
    VideoUpsert,
)
from youtube_knowledge_manager.services.library_optimization import LibraryOptimizationService


def _video(repository: VideoRepository, youtube_id: str):
    return repository.upsert(
        VideoUpsert(
            youtube_video_id=youtube_id,
            canonical_url=f"https://www.youtube.com/watch?v={youtube_id}",
            title=youtube_id,
            content_fingerprint=youtube_id.ljust(64, "0"),
        )
    ).video


def _playlist(
    repository: PlaylistRepository,
    youtube_id: str,
    name: str,
    system_kind: str | None = None,
):
    return repository.upsert(
        PlaylistUpsert(
            youtube_playlist_id=youtube_id,
            name=name,
            canonical_url=f"https://www.youtube.com/playlist?list={youtube_id}",
            system_kind=system_kind,
        )
    ).playlist


def test_library_optimization_reports_safe_organization_signals(db_session: Session) -> None:
    video_repository = VideoRepository(db_session)
    playlist_repository = PlaylistRepository(db_session)
    first = _video(video_repository, "first")
    second = _video(video_repository, "second")
    third = _video(video_repository, "third")
    liked = _playlist(playlist_repository, "LL", "Liked videos", "liked")
    alpha = _playlist(playlist_repository, "PLA", "Alpha")
    beta = _playlist(playlist_repository, "PLB", "Beta")
    _playlist(playlist_repository, "EMPTY", "Empty")
    for playlist, video in [
        (alpha, first),
        (beta, first),
        (alpha, second),
        (liked, third),
        (liked, first),
    ]:
        playlist_repository.upsert_membership(playlist=playlist, video=video, position=1)

    category = CategoryRepository(db_session).upsert(
        name="Beta",
        slug="beta",
        description=None,
        youtube_playlist_name="Beta",
        youtube_playlist_id="PLB",
    )
    classifications = ClassificationRepository(db_session)
    for video in [first, second]:
        classifications.assign(
            video=video,
            category=category,
            assignment_type=AssignmentType.RULE,
            confidence=1.0,
            is_primary=True,
            explanation="test",
            identifier="test",
            approved=True,
        )
    db_session.commit()

    report = LibraryOptimizationService(db_session).analyze(oversized_threshold=1)

    assert report.summary.playlist_count == 4
    assert report.summary.active_membership_count == 5
    assert report.summary.unique_video_count == 3
    assert report.summary.duplicate_regular_video_count == 1
    assert report.summary.uncategorized_video_count == 1
    assert report.summary.empty_regular_playlist_count == 1
    assert report.summary.oversized_playlist_count == 1
    assert report.summary.recommended_addition_count == 1
