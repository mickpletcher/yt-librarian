from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Error

import youtube_knowledge_manager.browser.external as external
from youtube_knowledge_manager.browser.external import (
    ExternalBrowserProcess,
    build_browser_command,
    connect_to_external_browser,
)


def test_build_browser_command_uses_dedicated_profile_and_loopback_debugging() -> None:
    command = build_browser_command(
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\project\data\browser-profile"),
        "about:blank",
        debugging_port=43123,
        headless=False,
    )

    assert "--user-data-dir=C:\\project\\data\\browser-profile" in command
    assert "--remote-debugging-address=127.0.0.1" in command
    assert "--remote-debugging-port=43123" in command
    assert "--headless=new" not in command
    assert command[-1] == "about:blank"


def test_manual_login_command_has_no_debugging_or_automation_flags() -> None:
    command = build_browser_command(
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\project\data\browser-profile"),
        "https://www.youtube.com/playlist?list=LL",
        debugging_port=None,
        headless=False,
    )

    assert not any(argument.startswith("--remote-debugging") for argument in command)
    assert "--enable-automation" not in command
    assert "--disable-blink-features=AutomationControlled" not in command


def test_headless_external_browser_uses_current_chromium_mode() -> None:
    command = build_browser_command(
        Path("google-chrome"),
        Path("data/browser-profile"),
        "about:blank",
        debugging_port=43123,
        headless=True,
    )

    assert "--headless=new" in command


@pytest.mark.asyncio
async def test_cdp_connection_retries_with_bounded_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    browser = object()
    connect = AsyncMock(side_effect=[Error("starting"), browser])
    playwright = SimpleNamespace(chromium=SimpleNamespace(connect_over_cdp=connect))
    launched = ExternalBrowserProcess(
        process=AsyncMock(),  # type: ignore[arg-type]
        debugging_port=43123,
    )
    monkeypatch.setattr(external.asyncio, "sleep", AsyncMock())

    connected = await connect_to_external_browser(  # type: ignore[arg-type]
        playwright,
        launched,
        timeout_seconds=10,
    )

    assert connected is browser
    assert connect.await_count == 2
    assert all(call.kwargs["timeout"] <= 5_000 for call in connect.await_args_list)
