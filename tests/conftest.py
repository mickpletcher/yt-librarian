from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.base import Base
from youtube_knowledge_manager.db.session import create_database_engine


@pytest.fixture
def db_session(tmp_path: Path) -> Iterator[Session]:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
