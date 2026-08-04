import streamlit as st

from youtube_knowledge_manager.db.session import create_session_factory
from youtube_knowledge_manager.settings import Settings, get_settings
from youtube_knowledge_manager.ui.pages import (
    categories,
    collection,
    dashboard,
    playlist_plan,
    review_queue,
    search,
)
from youtube_knowledge_manager.ui.pages import (
    settings as settings_page,
)


@st.cache_resource
def application_settings() -> Settings:
    settings = get_settings()
    settings.prepare_local_directories()
    return settings


def main() -> None:
    st.set_page_config(page_title="YouTube Knowledge Manager", layout="wide")
    settings = application_settings()
    factory = create_session_factory(settings)
    page_name = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Collection",
            "Categories",
            "Review Queue",
            "Playlist Plan",
            "Search",
            "Settings",
        ],
    )
    renderers = {
        "Dashboard": dashboard.render,
        "Collection": collection.render,
        "Categories": categories.render,
        "Review Queue": review_queue.render,
        "Playlist Plan": playlist_plan.render,
        "Search": search.render,
        "Settings": settings_page.render,
    }
    with factory() as session:
        renderers[page_name](session, settings)


if __name__ == "__main__":
    main()
