from pathlib import Path

import pytest

from youtube_knowledge_manager.operations.locking import (
    ApplicationLock,
    LockError,
    lock_path_for_database,
    read_lock_owner,
    remove_lock,
)


def _database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_application_lock_is_exclusive_and_releases(tmp_path: Path) -> None:
    database_url = _database_url(tmp_path / "app.sqlite3")
    lock_path = lock_path_for_database(database_url)

    with ApplicationLock(database_url, operation="test") as lock:
        assert lock_path.is_file()
        owner = read_lock_owner(lock_path)
        assert owner is not None
        assert owner.token == lock.owner.token
        with pytest.raises(LockError, match="Another operation"):
            with ApplicationLock(database_url, operation="second"):
                pass

    assert not lock_path.exists()


def test_stale_lock_removal_requires_force(tmp_path: Path) -> None:
    database_url = _database_url(tmp_path / "app.sqlite3")
    path = lock_path_for_database(database_url)
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(LockError, match="requires --force"):
        remove_lock(database_url, force=False)

    assert remove_lock(database_url, force=True) is True
    assert remove_lock(database_url, force=True) is False
