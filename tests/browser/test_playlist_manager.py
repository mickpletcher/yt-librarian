from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

import pytest

from youtube_knowledge_manager.browser.playlist_manager import PlaylistManager
from youtube_knowledge_manager.browser.selectors import Selectors


class Button:
    def __init__(self) -> None:
        self.first = self
        self.wait_for = AsyncMock()
        self.click = AsyncMock()


class Keyboard:
    def __init__(self) -> None:
        self.press = AsyncMock()


class Checkbox:
    def __init__(self, checked: bool = False) -> None:
        self.checked = checked
        self.click_count = 0

    async def get_attribute(self, name: str) -> str | None:
        assert name == "aria-checked"
        return "true" if self.checked else "false"

    async def click(self) -> None:
        self.click_count += 1
        self.checked = True


class Title:
    def __init__(self, value: str) -> None:
        self.value = value

    async def inner_text(self) -> str:
        return self.value


@dataclass
class Option:
    name: str
    playlist_id: str | None
    checkbox: Checkbox

    def locator(self, selector: str) -> Title | Checkbox:
        if selector == Selectors.PLAYLIST_OPTION_TITLE:
            return Title(self.name)
        assert selector == Selectors.PLAYLIST_OPTION_CHECKBOX
        return self.checkbox

    async def evaluate(self, _: str) -> str | None:
        return self.playlist_id


class Options:
    def __init__(self, values: list[Option]) -> None:
        self.values = values

    async def count(self) -> int:
        return len(self.values)

    def nth(self, index: int) -> Option:
        return self.values[index]


class Dialog:
    def __init__(self, options: Options) -> None:
        self.last = self
        self.options = options
        self.wait_for = AsyncMock()

    def locator(self, selector: str) -> Options:
        assert selector == Selectors.PLAYLIST_OPTION
        return self.options


class Page:
    def __init__(self, options: list[Option]) -> None:
        self.goto = AsyncMock()
        self.keyboard = Keyboard()
        self.button = Button()
        self.dialog = Dialog(Options(options))

    def locator(self, selector: str) -> Any:
        if selector == Selectors.SAVE_BUTTON:
            return self.button
        assert selector == Selectors.PLAYLIST_DIALOG
        return self.dialog


class Browser:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.ensure_safe_page = AsyncMock()
        self.pause_between_actions = AsyncMock()

    def require_page(self) -> Page:
        return self.page


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_add_requires_matching_playlist_id() -> None:
    wrong = Option("Target", "WRONG", Checkbox())
    correct = Option("Target", "PLTARGET", Checkbox())
    page = Page([wrong, correct])

    result = await PlaylistManager(Browser(page)).add_video(
        canonical_url="https://www.youtube.com/watch?v=video",
        playlist_name="Target",
        playlist_id="PLTARGET",
        dry_run=False,
    )

    assert result.changed is True
    assert wrong.checkbox.click_count == 0
    assert correct.checkbox.click_count == 1


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_add_fails_closed_when_id_is_not_exposed() -> None:
    page = Page([Option("Target", None, Checkbox())])

    with pytest.raises(LookupError, match="could not be verified"):
        await PlaylistManager(Browser(page)).add_video(
            canonical_url="https://www.youtube.com/watch?v=video",
            playlist_name="Target",
            playlist_id="PLTARGET",
            dry_run=False,
        )


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_add_rejects_ambiguous_name_without_id() -> None:
    page = Page(
        [
            Option("Duplicate", "PL1", Checkbox()),
            Option("Duplicate", "PL2", Checkbox()),
        ]
    )

    with pytest.raises(RuntimeError, match="ambiguous"):
        await PlaylistManager(Browser(page)).add_video(
            canonical_url="https://www.youtube.com/watch?v=video",
            playlist_name="Duplicate",
            dry_run=False,
        )


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_add_treats_existing_membership_as_success() -> None:
    checkbox = Checkbox(checked=True)
    page = Page([Option("Target", "PLTARGET", checkbox)])

    result = await PlaylistManager(Browser(page)).add_video(
        canonical_url="https://www.youtube.com/watch?v=video",
        playlist_name="Target",
        playlist_id="PLTARGET",
        dry_run=False,
    )

    assert result.already_present is True
    assert checkbox.click_count == 0
