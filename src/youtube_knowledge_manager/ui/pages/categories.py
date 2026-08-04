import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.services.category_service import CategoryService
from youtube_knowledge_manager.settings import Settings


def render(session: Session, _: Settings) -> None:
    st.header("Categories")
    rows = [
        {
            "Name": category.name,
            "Slug": category.slug,
            "Parent": category.parent.slug if category.parent else "",
            "Playlist": category.youtube_playlist_name or category.youtube_playlist_id or "",
            "Enabled": category.enabled,
        }
        for category in CategoryService(session).list_enabled()
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
