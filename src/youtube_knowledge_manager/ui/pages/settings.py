import streamlit as st
from sqlalchemy.orm import Session

from youtube_knowledge_manager.settings import Settings


def render(_: Session, settings: Settings) -> None:
    st.header("Settings")
    st.json(
        {
            "database_url": settings.database_url,
            "browser_profile_dir": str(settings.browser_profile_dir),
            "browser_channel": settings.browser_channel,
            "headless": settings.headless,
            "dry_run": settings.dry_run,
            "allow_playlist_removals": settings.allow_playlist_removals,
            "action_delay_seconds": [
                settings.min_action_delay_seconds,
                settings.max_action_delay_seconds,
            ],
            "ai_provider": settings.ai_provider,
            "ai_model": settings.ai_model,
        }
    )
    st.caption("Secrets are intentionally omitted. Edit the private .env file and restart the app.")
