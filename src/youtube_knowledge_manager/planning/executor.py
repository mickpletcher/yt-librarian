from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.playlist_manager import PlaylistManager
from youtube_knowledge_manager.browser.session import BrowserSession, ManualInterventionRequired
from youtube_knowledge_manager.db.base import utc_now
from youtube_knowledge_manager.db.models import ActionStatus
from youtube_knowledge_manager.db.repositories import BrowserActionRepository
from youtube_knowledge_manager.settings import Settings


@dataclass(frozen=True)
class ExecutionSummary:
    attempted: int
    succeeded: int
    failed: int


class PlaylistPlanExecutor:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.session = session
        self.actions = BrowserActionRepository(session)

    async def execute(self, *, limit: int = 100) -> ExecutionSummary:
        pending = self.actions.list_pending(limit=limit)
        attempted = 0
        succeeded = 0
        failed = 0
        async with BrowserSession(self.settings) as browser:
            manager = PlaylistManager(browser)
            for action in pending:
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
                except Exception as exc:
                    action.status = ActionStatus.FAILED
                    action.error_information = str(exc)
                    failed += 1
                self.session.commit()
                await browser.pause_between_actions()
        return ExecutionSummary(attempted=attempted, succeeded=succeeded, failed=failed)
