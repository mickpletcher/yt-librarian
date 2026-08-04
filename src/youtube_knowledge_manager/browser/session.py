from __future__ import annotations

import asyncio
import secrets
from contextlib import AbstractAsyncContextManager
from types import TracebackType

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from youtube_knowledge_manager.browser.profile import validate_profile_directory
from youtube_knowledge_manager.browser.selectors import SECURITY_URL_PARTS, Selectors
from youtube_knowledge_manager.settings import Settings


class ManualInterventionRequired(RuntimeError):
    pass


class BrowserSession(AbstractAsyncContextManager["BrowserSession"]):
    def __init__(self, settings: Settings, *, login_mode: bool = False) -> None:
        self.settings = settings
        self.login_mode = login_mode
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def __aenter__(self) -> BrowserSession:
        profile_dir = validate_profile_directory(self.settings.browser_profile_dir)
        self.playwright = await async_playwright().start()
        channel = (
            None if self.settings.browser_channel == "chromium" else self.settings.browser_channel
        )
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel=channel,
            headless=self.settings.headless,
            viewport={"width": 1440, "height": 1000},
            locale="en-US",
        )
        self.context.set_default_timeout(10_000)
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.context is not None:
            await self.context.close()
        if self.playwright is not None:
            await self.playwright.stop()

    def require_page(self) -> Page:
        if self.page is None:
            raise RuntimeError("Browser session has not been opened")
        return self.page

    async def pause_between_actions(self) -> None:
        delay = secrets.SystemRandom().uniform(
            self.settings.min_action_delay_seconds,
            self.settings.max_action_delay_seconds,
        )
        await asyncio.sleep(delay)

    async def ensure_safe_page(self) -> None:
        page = self.require_page()
        current_url = page.url.lower()
        if any(part in current_url for part in SECURITY_URL_PARTS) and not self.login_mode:
            raise ManualInterventionRequired(
                f"Login or account security page detected at {page.url}. "
                "Run browser-login manually."
            )
        checks = [
            (Selectors.CAPTCHA, "CAPTCHA"),
            (Selectors.CONSENT_DIALOG, "consent dialog"),
            (Selectors.SECURITY_PROMPT, "account security prompt"),
        ]
        if not self.login_mode:
            checks.append((Selectors.LOGIN_FORM, "login prompt"))
        for selector, label in checks:
            if await page.locator(selector).count() > 0:
                raise ManualInterventionRequired(
                    f"YouTube presented a {label}. Use browser-login and resolve it manually."
                )
