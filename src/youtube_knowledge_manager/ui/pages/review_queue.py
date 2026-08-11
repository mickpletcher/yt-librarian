import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.operations.locking import ApplicationLock
from youtube_knowledge_manager.services.review_service import ReviewService
from youtube_knowledge_manager.settings import Settings


def render(session: Session, settings: Settings) -> None:
    st.header("Review Queue")
    service = ReviewService(session)
    queue = service.queue()
    unassigned = service.unassigned()
    if not queue and not unassigned:
        st.info("No classification assignments need review.")
        return
    for assignment in queue:
        with st.container(border=True):
            st.subheader(assignment.video.title)
            st.write(f"Proposed category: {assignment.category.name} ({assignment.confidence:.0%})")
            st.caption(assignment.explanation or "No explanation")
            approve, reject, link = st.columns([1, 1, 4])
            if approve.button("Approve", key=f"approve-{assignment.id}"):
                with ApplicationLock(settings.database_url, operation="UI classification review"):
                    service.decide(assignment.id, approved=True)
                st.rerun()
            if reject.button("Reject", key=f"reject-{assignment.id}"):
                with ApplicationLock(settings.database_url, operation="UI classification review"):
                    service.decide(assignment.id, approved=False)
                st.rerun()
            link.link_button("Open video", assignment.video.canonical_url)
    if unassigned:
        st.subheader("Unclassified videos")
        categories = service.categories.list_enabled()
        category_names = {category.name: category.id for category in categories}
        for video in unassigned:
            with st.container(border=True):
                st.write(video.title)
                selected = st.selectbox(
                    "Assign category",
                    list(category_names),
                    key=f"category-{video.id}",
                )
                if st.button("Assign", key=f"assign-{video.id}"):
                    with ApplicationLock(
                        settings.database_url, operation="UI manual classification"
                    ):
                        service.assign_manual(video.id, category_names[selected], is_primary=True)
                    st.rerun()
