from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.session import BrowserSession
from youtube_knowledge_manager.collection.crawler import Crawler, CrawlSummary
from youtube_knowledge_manager.db.repositories import SyncRunRepository
from youtube_knowledge_manager.logging_config import get_logger
from youtube_knowledge_manager.settings import Settings


@dataclass(frozen=True)
class SyncSummary:
    seen: int
    created: int
    changed: int
    dry_run: bool


class SynchronizationService:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.session = session
        self.runs = SyncRunRepository(session)
        self.log = get_logger(component="synchronization")

    async def run(
        self,
        *,
        dry_run: bool,
        progress: Callable[[CrawlSummary], None] | None = None,
    ) -> SyncSummary:
        run = None
        if not dry_run:
            self.runs.recover_interrupted(operation="liked_videos")
            run = self.runs.start(dry_run=False)
            self.session.commit()
        try:
            async with BrowserSession(self.settings) as browser:
                crawl: CrawlSummary = await Crawler(
                    self.session,
                    dry_run=dry_run,
                    progress=progress,
                ).run(browser)
            if run is not None:
                run.videos_seen = crawl.seen
                run.videos_created = crawl.created
                run.videos_changed = crawl.changed
                self.runs.finish(run)
                self.session.commit()
            self.log.info(
                "sync_complete",
                seen=crawl.seen,
                created=crawl.created,
                changed=crawl.changed,
                dry_run=dry_run,
            )
            return SyncSummary(
                seen=crawl.seen,
                created=crawl.created,
                changed=crawl.changed,
                dry_run=dry_run,
            )
        except (KeyboardInterrupt, asyncio.CancelledError):
            if run is not None:
                self.runs.finish(run, failed=True, error="Synchronization interrupted")
                self.session.commit()
            raise
        except Exception as exc:
            if run is not None:
                self.runs.finish(run, failed=True, error=str(exc))
                self.session.commit()
            self.log.exception("sync_failed", error=str(exc))
            raise
