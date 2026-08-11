from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from youtube_knowledge_manager.operations.locking import sqlite_database_path


@dataclass(frozen=True)
class DatabaseCheckResult:
    integrity: str
    page_count: int
    freelist_count: int


def _connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path, timeout=30)


def check_database(database_url: str) -> DatabaseCheckResult:
    path = sqlite_database_path(database_url)
    if not path.is_file():
        raise FileNotFoundError(f"Database does not exist: {path}")
    with closing(_connect(path)) as connection:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        freelist_count = int(connection.execute("PRAGMA freelist_count").fetchone()[0])
    return DatabaseCheckResult(
        integrity=integrity,
        page_count=page_count,
        freelist_count=freelist_count,
    )


def backup_database(database_url: str, destination: Path) -> Path:
    source = sqlite_database_path(database_url)
    destination = destination.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Database does not exist: {source}")
    if destination == source:
        raise ValueError("Backup destination must differ from the active database")
    if destination.exists():
        raise FileExistsError(f"Backup already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with (
            closing(_connect(source)) as source_connection,
            closing(_connect(destination)) as target_connection,
        ):
            source_connection.backup(target_connection)
        result = check_sqlite_file(destination)
        if result.integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {result.integrity}")
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination


def check_sqlite_file(path: Path) -> DatabaseCheckResult:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"SQLite file does not exist: {resolved}")
    with closing(_connect(resolved)) as connection:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        freelist_count = int(connection.execute("PRAGMA freelist_count").fetchone()[0])
    return DatabaseCheckResult(integrity, page_count, freelist_count)


def restore_database(database_url: str, source: Path, *, apply: bool) -> Path:
    if not apply:
        raise ValueError("Restore requires explicit apply authorization")
    destination = sqlite_database_path(database_url)
    source = source.expanduser().resolve()
    if source == destination:
        raise ValueError("Restore source must differ from the active database")
    check = check_sqlite_file(source)
    if check.integrity != "ok":
        raise RuntimeError(f"Restore source integrity check failed: {check.integrity}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.restore-tmp")
    temporary.unlink(missing_ok=True)
    try:
        with (
            closing(_connect(source)) as source_connection,
            closing(_connect(temporary)) as target_connection,
        ):
            source_connection.backup(target_connection)
        restored = check_sqlite_file(temporary)
        if restored.integrity != "ok":
            raise RuntimeError(f"Restored database integrity check failed: {restored.integrity}")
        with (
            closing(_connect(temporary)) as source_connection,
            closing(_connect(destination)) as target_connection,
        ):
            source_connection.backup(target_connection)
        final = check_sqlite_file(destination)
        if final.integrity != "ok":
            raise RuntimeError(f"Active database integrity check failed: {final.integrity}")
        temporary.unlink()
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination
