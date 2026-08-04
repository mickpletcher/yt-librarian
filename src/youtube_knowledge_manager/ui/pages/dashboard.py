import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.services.video_service import VideoService
from youtube_knowledge_manager.settings import Settings


def render(session: Session, _: Settings) -> None:
    st.title("YouTube Knowledge Manager")
    summary = VideoService(session).dashboard()
    columns = st.columns(4)
    columns[0].metric("Videos", summary.total_videos)
    columns[1].metric("Review items", summary.review_items)
    columns[2].metric("Pending playlist actions", summary.pending_actions)
    columns[3].metric("Last sync", summary.last_sync_status or "Never")
    st.caption("Local data only. YouTube writes require explicit apply mode.")
