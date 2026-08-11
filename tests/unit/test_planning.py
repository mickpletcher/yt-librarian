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
from youtube_knowledge_manager.planning.playlist_plan import PlaylistPlanner


def test_playlist_plan_is_idempotent(db_session: Session) -> None:
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="abc",
                canonical_url="https://www.youtube.com/watch?v=abc",
                title="Video",
                content_fingerprint="a" * 64,
            )
        )
        .video
    )
    category = CategoryRepository(db_session).upsert(
        name="Software",
        slug="software",
        description=None,
        youtube_playlist_name="Knowledge - Software",
    )
    ClassificationRepository(db_session).assign(
        video=video,
        category=category,
        assignment_type=AssignmentType.RULE,
        confidence=0.95,
        is_primary=True,
        explanation="test",
        identifier="test-rule",
        approved=True,
    )
    db_session.commit()

    first, _ = PlaylistPlanner(db_session).generate(dry_run=False, persist=True)
    second, _ = PlaylistPlanner(db_session).generate(dry_run=False, persist=True)

    assert first.created_actions == 1
    assert second.created_actions == 0
    assert second.existing_actions == 1


def test_playlist_plan_skips_known_active_membership(db_session: Session) -> None:
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="already",
                canonical_url="https://www.youtube.com/watch?v=already",
                title="Already organized",
                content_fingerprint="b" * 64,
            )
        )
        .video
    )
    category = CategoryRepository(db_session).upsert(
        name="Software",
        slug="software-present",
        description=None,
        youtube_playlist_name="Knowledge - Software",
        youtube_playlist_id="PLSOFTWARE",
    )
    ClassificationRepository(db_session).assign(
        video=video,
        category=category,
        assignment_type=AssignmentType.RULE,
        confidence=0.95,
        is_primary=True,
        explanation="test",
        identifier="test-rule",
        approved=True,
    )
    playlists = PlaylistRepository(db_session)
    playlist = playlists.upsert(
        PlaylistUpsert(
            youtube_playlist_id="PLSOFTWARE",
            name="Knowledge - Software",
            canonical_url="https://www.youtube.com/playlist?list=PLSOFTWARE",
        )
    ).playlist
    playlists.upsert_membership(playlist=playlist, video=video, position=1)
    db_session.commit()

    summary, _ = PlaylistPlanner(db_session).generate(dry_run=False, persist=True)

    assert summary.created_actions == 0
    assert summary.already_present == 1
