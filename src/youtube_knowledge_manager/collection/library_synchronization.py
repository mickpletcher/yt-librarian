from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

from playwright.async_api import Error as PlaywrightError
from sqlalchemy.orm import Session

from youtube_knowledge_manager.browser.liked_videos import (
    CollectedVideo,
    PlaylistLoadError,
    PlaylistVideosCollector,
)
from youtube_knowledge_manager.browser.playlists import (
    DiscoveredPlaylist,
    PlaylistLibraryCollector,
)
from youtube_knowledge_manager.browser.session import BrowserSession
from youtube_knowledge_manager.collection.crawler import content_fingerprint, parse_duration_seconds
from youtube_knowledge_manager.db.models import YouTubePlaylist
from youtube_knowledge_manager.db.repositories import (
    PlaylistRepository,
    PlaylistUpsert,
    SyncRunRepository,
    VideoRepository,
    VideoUpsert,
)
from youtube_knowledge_manager.logging_config import get_logger
from youtube_knowledge_manager.settings import Settings


@dataclass(frozen=True)
class LibrarySyncSummary:
    discovery_complete: bool
    playlists_discovered: int
    playlists_seen: int
    playlists_failed: int
    playlists_created: int
    playlists_changed: int
    memberships_seen: int
    memberships_created: int
    memberships_deactivated: int
    unique_videos_seen: int
    videos_created: int
    videos_changed: int
    dry_run: bool


@dataclass(frozen=True)
class LibrarySyncProgress:
    playlists_completed: int
    playlists_total: int
    memberships_seen: int


class IncompletePlaylistLibraryError(RuntimeError):
    pass


def select_limited_playlists(
    playlists: list[DiscoveredPlaylist], limit: int | None
) -> list[DiscoveredPlaylist]:
    if limit is None:
        return playlists
    return sorted(
        playlists,
        key=lambda playlist: (
            playlist.system_kind is not None,
            playlist.reported_video_count is None,
            playlist.reported_video_count or 0,
            playlist.name.casefold(),
        ),
    )[:limit]


class LibrarySynchronizationService:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.session = session
        self.videos = VideoRepository(session)
        self.playlists = PlaylistRepository(session)
        self.runs = SyncRunRepository(session)
        self.log = get_logger(component="library_synchronization")

    async def run(
        self,
        *,
        dry_run: bool,
        limit_playlists: int | None = None,
        expected_playlist_count: int | None = None,
        progress: Callable[[LibrarySyncProgress], None] | None = None,
    ) -> LibrarySyncSummary:
        run = None
        if not dry_run:
            if limit_playlists is None and expected_playlist_count is None:
                raise ValueError(
                    "A full write-enabled library sync requires an explicit expected playlist "
                    "count. Run a read-only preview, then pass --expect-playlists."
                )
            self.runs.recover_interrupted(operation="saved_library")
            run = self.runs.start(dry_run=False, operation="saved_library")
            self.session.commit()
        try:
            summary = await self._run_core(
                dry_run=dry_run,
                limit_playlists=limit_playlists,
                expected_playlist_count=expected_playlist_count,
                progress=progress,
            )
            if run is not None:
                run.videos_seen = summary.memberships_seen
                run.videos_created = summary.videos_created
                run.videos_changed = summary.videos_changed
                self.runs.finish(run)
                self.session.commit()
            return summary
        except (KeyboardInterrupt, asyncio.CancelledError):
            if run is not None:
                self.runs.finish(run, failed=True, error="Library synchronization interrupted")
                self.session.commit()
            raise
        except Exception as exc:
            if run is not None:
                self.runs.finish(run, failed=True, error=str(exc))
                self.session.commit()
            raise

    async def _run_core(
        self,
        *,
        dry_run: bool,
        limit_playlists: int | None,
        expected_playlist_count: int | None,
        progress: Callable[[LibrarySyncProgress], None] | None,
    ) -> LibrarySyncSummary:
        playlist_failures = 0
        playlists_created = 0
        playlists_changed = 0
        memberships_seen = 0
        memberships_created = 0
        memberships_deactivated = 0
        videos_created = 0
        videos_changed = 0
        unique_video_ids: set[str] = set()

        async with BrowserSession(self.settings) as browser:
            discovery = await PlaylistLibraryCollector(browser).collect()
            if (
                expected_playlist_count is not None
                and len(discovery.playlists) != expected_playlist_count
            ):
                raise IncompletePlaylistLibraryError(
                    f"Expected {expected_playlist_count} saved playlists but discovered "
                    f"{len(discovery.playlists)}. No playlist processing started."
                )
            if not discovery.complete and limit_playlists is None:
                raise IncompletePlaylistLibraryError(
                    "Saved playlist discovery stopped incomplete after "
                    f"{len(discovery.playlists)} visible playlists; "
                    f"reason={discovery.termination_reason}. No complete-library result was "
                    "recorded."
                )
            discovered = discovery.playlists
            playlists_discovered = len(discovered)
            discovered = select_limited_playlists(discovered, limit_playlists)

            for playlist_index, discovered_playlist in enumerate(discovered, start=1):
                if progress is not None:
                    progress(
                        LibrarySyncProgress(
                            playlists_completed=playlist_index - 1,
                            playlists_total=len(discovered),
                            memberships_seen=memberships_seen,
                        )
                    )
                playlist_record = None
                if not dry_run:
                    playlist_result = self.playlists.upsert(
                        PlaylistUpsert(
                            youtube_playlist_id=discovered_playlist.youtube_playlist_id,
                            name=discovered_playlist.name,
                            canonical_url=discovered_playlist.canonical_url,
                            system_kind=discovered_playlist.system_kind,
                            reported_video_count=discovered_playlist.reported_video_count,
                        )
                    )
                    playlist_record = playlist_result.playlist
                    playlists_created += int(playlist_result.created)
                    playlists_changed += int(
                        playlist_result.changed and not playlist_result.created
                    )
                    self.session.commit()

                observed_database_video_ids: set[int] = set()

                async def persist(
                    video: CollectedVideo,
                    current_playlist: YouTubePlaylist | None = playlist_record,
                    current_observed_ids: set[int] = observed_database_video_ids,
                ) -> None:
                    nonlocal memberships_seen, memberships_created
                    nonlocal videos_created, videos_changed
                    memberships_seen += 1
                    unique_video_ids.add(video.youtube_video_id)
                    if dry_run or current_playlist is None:
                        return
                    video_result = self.videos.upsert(
                        VideoUpsert(
                            youtube_video_id=video.youtube_video_id,
                            canonical_url=video.canonical_url,
                            title=video.title,
                            channel_id=video.channel_id,
                            channel_name=video.channel_name,
                            duration_seconds=parse_duration_seconds(video.duration_text),
                            thumbnail_url=video.thumbnail_url,
                            content_fingerprint=content_fingerprint(video),
                            raw_metadata=video.raw_metadata,
                        )
                    )
                    videos_created += int(video_result.created)
                    videos_changed += int(video_result.changed and not video_result.created)
                    current_observed_ids.add(video_result.video.id)
                    _, created = self.playlists.upsert_membership(
                        playlist=current_playlist,
                        video=video_result.video,
                        position=video.position,
                    )
                    memberships_created += int(created)
                    self.session.commit()

                try:
                    crawl_result = await PlaylistVideosCollector(
                        browser,
                        discovered_playlist.youtube_playlist_id,
                        expected_video_count=discovered_playlist.reported_video_count,
                    ).collect(on_video=persist)
                except (PlaylistLoadError, PlaywrightError):
                    playlist_failures += 1
                    self.log.warning("playlist_skipped_after_load_failure")
                    continue

                if not crawl_result.complete:
                    playlist_failures += 1
                    self.log.warning(
                        "playlist_membership_reconciliation_skipped",
                        reason=crawl_result.termination_reason,
                        expected_count=discovered_playlist.reported_video_count,
                        observed_count=len(crawl_result.videos),
                    )
                    continue

                if not dry_run and playlist_record is not None:
                    memberships_deactivated += self.playlists.deactivate_missing(
                        playlist=playlist_record,
                        observed_video_ids=observed_database_video_ids,
                    )
                    self.session.commit()

        summary = LibrarySyncSummary(
            discovery_complete=discovery.complete,
            playlists_discovered=playlists_discovered,
            playlists_seen=len(discovered),
            playlists_failed=playlist_failures,
            playlists_created=playlists_created,
            playlists_changed=playlists_changed,
            memberships_seen=memberships_seen,
            memberships_created=memberships_created,
            memberships_deactivated=memberships_deactivated,
            unique_videos_seen=len(unique_video_ids),
            videos_created=videos_created,
            videos_changed=videos_changed,
            dry_run=dry_run,
        )
        if progress is not None:
            progress(
                LibrarySyncProgress(
                    playlists_completed=len(discovered),
                    playlists_total=len(discovered),
                    memberships_seen=memberships_seen,
                )
            )
        self.log.info("library_sync_complete", **summary.__dict__)
        return summary
