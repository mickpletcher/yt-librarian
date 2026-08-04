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

    tables = set(inspect(create_database_engine(f"sqlite:///{database_path}")).get_table_names())
    assert {
        "videos",
        "transcripts",
        "categories",
        "video_categories",
        "classification_runs",
        "classification_rules",
        "sync_runs",
        "browser_actions",
    } <= tables
