from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

import youtube_knowledge_manager.ui.app as ui_app
from youtube_knowledge_manager.settings import Settings
from youtube_knowledge_manager.ui.pages import (
    categories,
    collection,
    dashboard,
    library_optimization,
    playlist_plan,
    review_queue,
    search,
)
from youtube_knowledge_manager.ui.pages import settings as settings_page


class FakeColumn:
    def metric(self, *_: object, **__: object) -> None:
        pass

    def button(self, *_: object, **__: object) -> bool:
        return False

    def link_button(self, *_: object, **__: object) -> None:
        pass


class FakeStreamlit:
    def __init__(self) -> None:
        self.sidebar = SimpleNamespace(radio=lambda *_args, **_kwargs: "Dashboard")

    def __getattr__(self, _: str):  # type: ignore[no-untyped-def]
        return MagicMock()

    def radio(self, *_: object, **__: object) -> str:
        return "Liked Videos"

    def checkbox(self, *_: object, **__: object) -> bool:
        return False

    def button(self, *_: object, **__: object) -> bool:
        return False

    def number_input(self, *_: object, **__: object) -> int:
        return 500

    def text_input(self, *_: object, **__: object) -> str:
        return ""

    def selectbox(self, _: str, options: list[str], **__: object) -> str:
        return options[0]

    def columns(self, specification):  # type: ignore[no-untyped-def]
        count = specification if isinstance(specification, int) else len(specification)
        return [FakeColumn() for _ in range(count)]


def test_all_streamlit_pages_render_empty_state(db_session: Session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeStreamlit()
    settings = Settings(database_url="sqlite:///:memory:")
    modules = [
        categories,
        collection,
        dashboard,
        library_optimization,
        playlist_plan,
        review_queue,
        search,
        settings_page,
    ]
    for module in modules:
        monkeypatch.setattr(module, "st", fake)
        module.render(db_session, settings)


def test_app_routes_to_selected_page(db_session: Session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    fake = FakeStreamlit()
    render = MagicMock()
    monkeypatch.setattr(ui_app, "st", fake)
    monkeypatch.setattr(ui_app, "application_settings", Settings)
    monkeypatch.setattr(ui_app, "create_session_factory", lambda _: lambda: nullcontext(db_session))
    monkeypatch.setattr(ui_app.dashboard, "render", render)

    ui_app.main()

    render.assert_called_once()
