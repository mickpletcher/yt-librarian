from unittest.mock import AsyncMock, MagicMock

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from youtube_knowledge_manager.browser.liked_videos import LikedVideosCollector
from youtube_knowledge_manager.browser.session import ManualInterventionRequired


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_load_retries_after_hydration_timeout() -> None:
    browser = MagicMock()
    browser.ensure_safe_page = AsyncMock()
    browser.pause_between_actions = AsyncMock()
    page = MagicMock()
    page.goto = AsyncMock()
    page.locator.return_value.first.wait_for = AsyncMock(
        side_effect=[PlaywrightTimeoutError("slow hydration"), None]
    )

    await LikedVideosCollector(browser)._open_playlist(page)

    assert page.goto.await_count == 2
    browser.pause_between_actions.assert_awaited_once()
    assert browser.ensure_safe_page.await_count == 4


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_load_stops_when_retry_detects_sign_in() -> None:
    browser = MagicMock()
    browser.ensure_safe_page = AsyncMock(
        side_effect=[None, ManualInterventionRequired("login prompt")]
    )
    browser.pause_between_actions = AsyncMock()
    page = MagicMock()
    page.goto = AsyncMock()
    page.locator.return_value.first.wait_for = AsyncMock(
        side_effect=PlaywrightTimeoutError("slow hydration")
    )

    with pytest.raises(ManualInterventionRequired, match="login prompt"):
        await LikedVideosCollector(browser)._open_playlist(page)

    assert page.goto.await_count == 1
    browser.pause_between_actions.assert_not_awaited()
