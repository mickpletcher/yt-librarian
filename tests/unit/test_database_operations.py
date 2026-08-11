import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from youtube_knowledge_manager.services.database_operations import (
    backup_database,
    check_database,
    restore_database,
)


def _database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _create_database(path: Path, value: str) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample VALUES (?)", (value,))
        connection.commit()


def _read_value(path: Path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        return str(connection.execute("SELECT value FROM sample").fetchone()[0])


def test_backup_and_restore_are_integrity_checked(tmp_path: Path) -> None:
    active = tmp_path / "active.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    _create_database(active, "original")

    assert check_database(_database_url(active)).integrity == "ok"
    assert backup_database(_database_url(active), backup) == backup.resolve()
    assert _read_value(backup) == "original"

    with closing(sqlite3.connect(active)) as connection:
        connection.execute("UPDATE sample SET value = 'changed'")
        connection.commit()

    restore_database(_database_url(active), backup, apply=True)
    assert _read_value(active) == "original"


def test_backup_and_restore_reject_unsafe_targets(tmp_path: Path) -> None:
    active = tmp_path / "active.sqlite3"
    _create_database(active, "value")

    with pytest.raises(ValueError, match="must differ"):
        backup_database(_database_url(active), active)
    with pytest.raises(ValueError, match="explicit apply"):
        restore_database(_database_url(active), tmp_path / "missing.sqlite3", apply=False)
