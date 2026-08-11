from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.orm import Session

import youtube_knowledge_manager.collection.synchronization as synchronization
from youtube_knowledge_manager.collection.synchronization import SynchronizationService
from youtube_knowledge_manager.db.models import SyncStatus
from youtube_knowledge_manager.db.repositories import SyncRunRepository
from youtube_knowledge_manager.settings import Settings


class BrowserSession:
    def __init__(self, _: Settings) -> None:
        pass

    async def __aenter__(self) -> BrowserSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


@pytest.mark.asyncio
async def test_interrupted_sync_records_failed_run(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Crawler:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def run(self, _: object) -> None:
            raise asyncio.CancelledError

    monkeypatch.setattr(synchronization, "BrowserSession", BrowserSession)
    monkeypatch.setattr(synchronization, "Crawler", Crawler)

    with pytest.raises(asyncio.CancelledError):
        await SynchronizationService(Settings(), db_session).run(dry_run=False)

    run = SyncRunRepository(db_session).latest()
    assert run is not None
    assert run.status == SyncStatus.FAILED
    assert run.error_information == "Synchronization interrupted"


def test_sync_run_recovery_marks_abandoned_run_failed(db_session: Session) -> None:
    repository = SyncRunRepository(db_session)
    abandoned = repository.start(dry_run=False, operation="saved_library")
    repository.start(dry_run=False, operation="liked_videos")
    db_session.commit()

    recovered = repository.recover_interrupted(operation="saved_library")
    db_session.commit()

    db_session.refresh(abandoned)
    assert recovered == 1
    assert abandoned.status == SyncStatus.FAILED
    assert abandoned.completed_at is not None
    assert abandoned.error_information == "Previous synchronization ended before completion"
