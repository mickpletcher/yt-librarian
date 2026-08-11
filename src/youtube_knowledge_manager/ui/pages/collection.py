import asyncio

import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.collection.crawler import CrawlSummary
from youtube_knowledge_manager.collection.library_synchronization import (
    LibrarySynchronizationService,
    LibrarySyncProgress,
)
from youtube_knowledge_manager.collection.synchronization import SynchronizationService
from youtube_knowledge_manager.operations.locking import ApplicationLock
from youtube_knowledge_manager.settings import Settings


def render(session: Session, settings: Settings) -> None:
    st.header("Collection")
    scope = st.radio("Scope", ["Liked Videos", "All saved playlists"], horizontal=True)
    write = st.checkbox("Persist discovered and changed videos", value=False)
    limit_playlists = None
    expected_playlist_count = None
    if scope == "All saved playlists":
        configured_limit = st.number_input(
            "Playlist limit (0 scans all)", min_value=0, value=0, step=1
        )
        limit_playlists = int(configured_limit) or None
        configured_expected = st.number_input(
            "Expected discovered playlist count (0 means not set)",
            min_value=0,
            value=0,
            step=1,
        )
        expected_playlist_count = int(configured_expected) or None
    if st.button("Start scan"):
        with st.spinner(
            "Scanning YouTube. Complete any manual prompts through browser-login first."
        ):
            try:
                with ApplicationLock(settings.database_url, operation="UI collection"):
                    progress_bar = st.progress(0, text="Starting collection")
                    if scope == "Liked Videos":

                        def report_liked(progress: CrawlSummary) -> None:
                            progress_bar.progress(
                                min(progress.seen / max(settings.max_scrolls, 1), 0.99),
                                text=f"Videos observed: {progress.seen}",
                            )

                        summary = asyncio.run(
                            SynchronizationService(settings, session).run(
                                dry_run=not write,
                                progress=report_liked,
                            )
                        )
                        progress_bar.progress(1.0, text="Collection complete")
                        st.success(
                            f"Seen {summary.seen}. Created {summary.created}. "
                            f"Changed {summary.changed}."
                        )
                    else:

                        def report_library(progress: LibrarySyncProgress) -> None:
                            denominator = max(progress.playlists_total, 1)
                            progress_bar.progress(
                                progress.playlists_completed / denominator,
                                text=(
                                    f"Playlists {progress.playlists_completed}/"
                                    f"{progress.playlists_total}; memberships "
                                    f"{progress.memberships_seen}"
                                ),
                            )

                        library_summary = asyncio.run(
                            LibrarySynchronizationService(settings, session).run(
                                dry_run=not write,
                                limit_playlists=limit_playlists,
                                expected_playlist_count=expected_playlist_count,
                                progress=report_library,
                            )
                        )
                        st.success(
                            f"Discovered {library_summary.playlists_discovered}. "
                            f"Processed {library_summary.playlists_seen}. "
                            f"Failed {library_summary.playlists_failed}. "
                            f"Memberships {library_summary.memberships_seen}. "
                            f"Unique videos {library_summary.unique_videos_seen}."
                        )
            except Exception as exc:
                st.error(str(exc))
