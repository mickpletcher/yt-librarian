import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import BrowserActionRepository
from youtube_knowledge_manager.operations.locking import ApplicationLock
from youtube_knowledge_manager.planning.playlist_plan import PlaylistPlanner
from youtube_knowledge_manager.settings import Settings


def render(session: Session, settings: Settings) -> None:
    st.header("Playlist Plan")
    st.warning(
        "This page creates local proposals only. Use `ykm apply-plan --apply` for YouTube writes."
    )
    persist = st.checkbox("Persist new proposed actions", value=False)
    if st.button("Generate plan"):
        with ApplicationLock(settings.database_url, operation="UI playlist planning"):
            summary, actions = PlaylistPlanner(session).generate(
                dry_run=not persist, persist=persist
            )
        del actions
        st.success(
            f"Eligible {summary.eligible_assignments}. New {summary.created_actions}. "
            f"Existing {summary.existing_actions}. Already present {summary.already_present}. "
            f"Unmapped {summary.skipped_unmapped}."
        )
    actions = BrowserActionRepository(session).list_recent()
    st.dataframe(
        [
            {
                "Video": action.video.title,
                "Playlist": action.target_playlist_name,
                "Status": action.status.value,
                "Attempts": action.attempts,
                "Error": action.error_information or "",
            }
            for action in actions
        ],
        use_container_width=True,
        hide_index=True,
    )
