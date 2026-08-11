import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.operations.locking import ApplicationLock
from youtube_knowledge_manager.planning.playlist_plan import PlaylistPlanner
from youtube_knowledge_manager.services.library_optimization import LibraryOptimizationService
from youtube_knowledge_manager.settings import Settings


def render(session: Session, settings: Settings) -> None:
    st.header("Library Optimization")
    st.caption("Analysis is local. Stored recommendations are add-only and do not change YouTube.")
    threshold = st.number_input("Oversized playlist threshold", min_value=1, value=500)
    report = LibraryOptimizationService(session).analyze(oversized_threshold=int(threshold))
    summary = report.summary
    columns = st.columns(4)
    columns[0].metric("Playlists", summary.playlist_count)
    columns[1].metric("Unique videos", summary.unique_video_count)
    columns[2].metric("Cross-playlist duplicates", summary.duplicate_regular_video_count)
    columns[3].metric("Uncategorized", summary.uncategorized_video_count)
    st.dataframe(
        [
            {
                "Playlist": row.playlist.name,
                "Videos": row.active_video_count,
                "Type": row.playlist.system_kind or "regular",
                "Reported": row.playlist.reported_video_count,
            }
            for row in report.playlists
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.write(
        f"Empty regular playlists: {summary.empty_regular_playlist_count}. "
        f"Oversized playlists: {summary.oversized_playlist_count}. "
        f"Recommended additions: {summary.recommended_addition_count}."
    )
    if st.button("Store add-only recommendations"):
        with ApplicationLock(settings.database_url, operation="UI optimization planning"):
            plan_summary, actions = PlaylistPlanner(session).generate(dry_run=False, persist=True)
        del actions
        st.success(
            f"New {plan_summary.created_actions}. Existing {plan_summary.existing_actions}. "
            f"Already present {plan_summary.already_present}. "
            f"Unmapped {plan_summary.skipped_unmapped}."
        )
