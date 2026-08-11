from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

import youtube_knowledge_manager.planning.executor as executor_module
from youtube_knowledge_manager.db.models import ActionStatus
from youtube_knowledge_manager.db.repositories import (
    BrowserActionRepository,
    CategoryRepository,
    PlaylistRepository,
    PlaylistUpsert,
    VideoRepository,
    VideoUpsert,
)
from youtube_knowledge_manager.planning.executor import PlaylistPlanExecutor
from youtube_knowledge_manager.settings import Settings


def _action(db_session: Session):  # type: ignore[no-untyped-def]
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="action-video",
                canonical_url="https://www.youtube.com/watch?v=action-video",
                title="Action",
                content_fingerprint="c" * 64,
            )
        )
        .video
    )
    category = CategoryRepository(db_session).upsert(
        name="Action",
        slug="action",
        description=None,
        youtube_playlist_name="Target",
        youtube_playlist_id="PLTARGET",
    )
    action, _ = BrowserActionRepository(db_session).get_or_create_add(
        video=video,
        category=category,
        dry_run=False,
    )
    db_session.commit()
    return action


class BrowserSession:
    def __init__(self, _: Settings) -> None:
        self.pause_between_actions = self.pause

    async def __aenter__(self) -> BrowserSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def pause(self) -> None:
        pass


@pytest.mark.asyncio
async def test_executor_passes_playlist_id_and_completes(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    action = _action(db_session)
    received: dict[str, object] = {}

    class Manager:
        def __init__(self, _: object) -> None:
            pass

        async def add_video(self, **kwargs: object) -> None:
            received.update(kwargs)

    monkeypatch.setattr(executor_module, "BrowserSession", BrowserSession)
    monkeypatch.setattr(executor_module, "PlaylistManager", Manager)

    summary = await PlaylistPlanExecutor(Settings(), db_session).execute(limit=1)

    assert summary.succeeded == 1
    assert action.status == ActionStatus.SUCCEEDED
    assert received["playlist_id"] == "PLTARGET"


@pytest.mark.asyncio
async def test_executor_marks_cancelled_action_failed(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    action = _action(db_session)

    class Manager:
        def __init__(self, _: object) -> None:
            pass

        async def add_video(self, **_: object) -> None:
            raise asyncio.CancelledError

    monkeypatch.setattr(executor_module, "BrowserSession", BrowserSession)
    monkeypatch.setattr(executor_module, "PlaylistManager", Manager)

    with pytest.raises(asyncio.CancelledError):
        await PlaylistPlanExecutor(Settings(), db_session).execute(limit=1)

    assert action.status == ActionStatus.FAILED
    assert action.error_information == "Execution interrupted before completion"


@pytest.mark.asyncio
async def test_validation_opens_dialog_without_changing_action_state(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    action = _action(db_session)
    received: dict[str, object] = {}

    class Manager:
        def __init__(self, _: object) -> None:
            pass

        async def add_video(self, **kwargs: object):  # type: ignore[no-untyped-def]
            received.update(kwargs)
            return SimpleNamespace(already_present=False)

    monkeypatch.setattr(executor_module, "BrowserSession", BrowserSession)
    monkeypatch.setattr(executor_module, "PlaylistManager", Manager)

    summary = await PlaylistPlanExecutor(Settings(), db_session).validate(limit=1)

    assert summary.succeeded == 1
    assert received["dry_run"] is True
    assert action.status == ActionStatus.PLANNED
    assert action.attempts == 0


def test_executor_recovers_actions_left_running(db_session: Session) -> None:
    action = _action(db_session)
    action.status = ActionStatus.RUNNING
    db_session.commit()

    recovered = BrowserActionRepository(db_session).recover_interrupted()

    assert recovered == 1
    assert action.status == ActionStatus.FAILED


@pytest.mark.asyncio
async def test_executor_skips_membership_already_in_inventory(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    action = _action(db_session)
    playlists = PlaylistRepository(db_session)
    playlist = playlists.upsert(
        PlaylistUpsert(
            youtube_playlist_id="PLTARGET",
            name="Target",
            canonical_url="https://www.youtube.com/playlist?list=PLTARGET",
        )
    ).playlist
    playlists.upsert_membership(playlist=playlist, video=action.video, position=1)
    db_session.commit()

    class UnexpectedBrowser:
        def __init__(self, _: Settings) -> None:
            raise AssertionError("Browser should not open")

    monkeypatch.setattr(executor_module, "BrowserSession", UnexpectedBrowser)

    summary = await PlaylistPlanExecutor(Settings(), db_session).execute(limit=1)

    assert summary.attempted == 0
    assert summary.already_present == 1
    assert action.status == ActionStatus.SUCCEEDED
