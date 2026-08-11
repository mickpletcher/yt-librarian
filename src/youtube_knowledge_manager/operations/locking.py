from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType

from sqlalchemy.engine import make_url


class LockError(RuntimeError):
    pass


@dataclass(frozen=True)
class LockOwner:
    token: str
    pid: int
    operation: str
    started_at: str


def sqlite_database_path(database_url: str) -> Path:
    url = make_url(database_url)
    if url.drivername != "sqlite" or not url.database or url.database == ":memory:":
        raise ValueError("This operation requires a file-backed SQLite database")
    return Path(url.database).expanduser().resolve()


def lock_path_for_database(database_url: str) -> Path:
    database_path = sqlite_database_path(database_url)
    return database_path.with_suffix(f"{database_path.suffix}.lock")


class ApplicationLock:
    def __init__(self, database_url: str, *, operation: str) -> None:
        self.path = lock_path_for_database(database_url)
        self.owner = LockOwner(
            token=uuid.uuid4().hex,
            pid=os.getpid(),
            operation=operation,
            started_at=datetime.now(UTC).isoformat(),
        )
        self.acquired = False

    def __enter__(self) -> ApplicationLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            owner = read_lock_owner(self.path)
            detail = (
                f"PID {owner.pid}, operation {owner.operation}, started {owner.started_at}"
                if owner is not None
                else "owner metadata unavailable"
            )
            raise LockError(
                f"Another operation owns the application lock ({detail}). "
                "Confirm it has stopped before using `ykm unlock --force`."
            ) from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(asdict(self.owner), handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        self.acquired = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self.acquired:
            return
        current = read_lock_owner(self.path)
        if current is not None and current.token == self.owner.token:
            self.path.unlink(missing_ok=True)
        self.acquired = False


def read_lock_owner(path: Path) -> LockOwner | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return LockOwner(
            token=str(payload["token"]),
            pid=int(payload["pid"]),
            operation=str(payload["operation"]),
            started_at=str(payload["started_at"]),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def remove_lock(database_url: str, *, force: bool) -> bool:
    if not force:
        raise LockError("Lock removal requires --force after confirming no operation is active")
    path = lock_path_for_database(database_url)
    if not path.exists():
        return False
    path.unlink()
    return True
