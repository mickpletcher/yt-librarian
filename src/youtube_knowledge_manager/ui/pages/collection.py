import asyncio

import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.collection.synchronization import SynchronizationService
from youtube_knowledge_manager.settings import Settings


def render(session: Session, settings: Settings) -> None:
    st.header("Collection")
    st.write("Scan the Liked Videos playlist using the dedicated authenticated profile.")
    write = st.checkbox("Persist discovered and changed videos", value=False)
    if st.button("Start scan"):
        with st.spinner(
            "Scanning YouTube. Complete any manual prompts through browser-login first."
        ):
            try:
                summary = asyncio.run(
                    SynchronizationService(settings, session).run(dry_run=not write)
                )
                st.success(
                    f"Seen {summary.seen}. Created {summary.created}. Changed {summary.changed}."
                )
            except Exception as exc:
                st.error(str(exc))
