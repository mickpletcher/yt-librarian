import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.search.semantic_search import get_semantic_search_status
from youtube_knowledge_manager.search.text_search import TextSearchService
from youtube_knowledge_manager.services.category_service import CategoryService
from youtube_knowledge_manager.settings import Settings


def render(session: Session, _: Settings) -> None:
    st.header("Search")
    categories = CategoryService(session).list_enabled()
    query = st.text_input("Title, description, or channel")
    selected = st.selectbox("Category", ["All", *[category.slug for category in categories]])
    results = TextSearchService(session).search(
        query=query, category_slug=None if selected == "All" else selected
    )
    st.caption(f"{len(results)} results")
    for result in results:
        st.markdown(f"[{result.title}]({result.canonical_url})")
        st.caption(result.channel_name or "Unknown channel")
        if result.summary:
            st.write(result.summary)
    semantic = get_semantic_search_status()
    st.info(semantic.reason)
