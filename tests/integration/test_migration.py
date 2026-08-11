from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from youtube_knowledge_manager.db.session import create_database_engine


@pytest.mark.integration
def test_initial_migration_creates_required_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "migration.sqlite3"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")

    engine = create_database_engine(f"sqlite:///{database_path}")
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {
            "videos",
            "transcripts",
            "categories",
            "video_categories",
            "classification_runs",
            "classification_rules",
            "sync_runs",
            "browser_actions",
            "youtube_playlists",
            "playlist_memberships",
        } <= tables
        transcript_columns = {column["name"] for column in inspector.get_columns("transcripts")}
        assert {"attempts", "last_attempted_at", "next_retry_at"} <= transcript_columns
        sync_columns = {column["name"] for column in inspector.get_columns("sync_runs")}
        assert "operation" in sync_columns
    finally:
        engine.dispose()


def test_alembic_honors_database_url_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured_path = tmp_path / "configured.sqlite3"
    environment_path = tmp_path / "environment.sqlite3"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{configured_path.as_posix()}")
    monkeypatch.setenv("YKM_DATABASE_URL", f"sqlite:///{environment_path.as_posix()}")

    command.upgrade(config, "head")

    assert environment_path.is_file()
    assert not configured_path.exists()
