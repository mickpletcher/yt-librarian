import asyncio
from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.playlist_manager import PlaylistManager
from youtube_knowledge_manager.browser.session import BrowserSession, ManualInterventionRequired
from youtube_knowledge_manager.db.base import utc_now
from youtube_knowledge_manager.db.models import ActionStatus
from youtube_knowledge_manager.db.repositories import BrowserActionRepository, PlaylistRepository
from youtube_knowledge_manager.settings import Settings


@dataclass(frozen=True)
class ExecutionSummary:
    attempted: int
    succeeded: int
    failed: int
    already_present: int


class PlaylistPlanExecutor:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.session = session
        self.actions = BrowserActionRepository(session)
        self.playlists = PlaylistRepository(session)

    async def execute(self, *, limit: int = 100) -> ExecutionSummary:
        self.actions.recover_interrupted()
        self.session.commit()
        pending = self.actions.list_pending(limit=limit)
        attempted = 0
        succeeded = 0
        failed = 0
        already_present = 0
        browser_actions = []
        for action in pending:
            if self.playlists.has_active_membership(
                video_id=action.video_id,
                youtube_playlist_id=action.target_playlist_id,
                playlist_name=action.target_playlist_name,
            ):
                action.status = ActionStatus.SUCCEEDED
                action.completed_at = utc_now()
                action.error_information = None
                already_present += 1
            else:
                browser_actions.append(action)
        self.session.commit()

        if not browser_actions:
            return ExecutionSummary(
                attempted=0,
                succeeded=0,
                failed=0,
                already_present=already_present,
            )

        async with BrowserSession(self.settings) as browser:
            manager = PlaylistManager(browser)
            for action in browser_actions:
                attempted += 1
                action.status = ActionStatus.RUNNING
                action.attempts += 1
                action.last_attempted_at = utc_now()
                action.dry_run = False
                self.session.commit()
                try:
                    await manager.add_video(
                        canonical_url=action.video.canonical_url,
                        playlist_name=action.target_playlist_name,
                        playlist_id=action.target_playlist_id,
                        dry_run=False,
                    )
                    action.status = ActionStatus.SUCCEEDED
                    action.completed_at = utc_now()
                    action.error_information = None
                    succeeded += 1
                except ManualInterventionRequired:
                    action.status = ActionStatus.FAILED
                    action.error_information = "Manual intervention required"
                    self.session.commit()
                    raise
                except (KeyboardInterrupt, asyncio.CancelledError):
                    action.status = ActionStatus.FAILED
                    action.error_information = "Execution interrupted before completion"
                    self.session.commit()
                    raise
                except Exception as exc:
                    action.status = ActionStatus.FAILED
                    action.error_information = str(exc)
                    failed += 1
                self.session.commit()
                await browser.pause_between_actions()
        return ExecutionSummary(
            attempted=attempted,
            succeeded=succeeded,
            failed=failed,
            already_present=already_present,
        )

    async def validate(self, *, limit: int = 100) -> ExecutionSummary:
        pending = self.actions.list_pending(limit=limit)
        attempted = 0
        validated = 0
        failed = 0
        already_present = 0
        if not pending:
            return ExecutionSummary(0, 0, 0, 0)
        async with BrowserSession(self.settings) as browser:
            manager = PlaylistManager(browser)
            for action in pending:
                if self.playlists.has_active_membership(
                    video_id=action.video_id,
                    youtube_playlist_id=action.target_playlist_id,
                    playlist_name=action.target_playlist_name,
                ):
                    already_present += 1
                    continue
                attempted += 1
                try:
                    result = await manager.add_video(
                        canonical_url=action.video.canonical_url,
                        playlist_name=action.target_playlist_name,
                        playlist_id=action.target_playlist_id,
                        dry_run=True,
                    )
                    if result.already_present:
                        already_present += 1
                    else:
                        validated += 1
                except ManualInterventionRequired:
                    raise
                except Exception:
                    failed += 1
                await browser.pause_between_actions()
        return ExecutionSummary(
            attempted=attempted,
            succeeded=validated,
            failed=failed,
            already_present=already_present,
        )
