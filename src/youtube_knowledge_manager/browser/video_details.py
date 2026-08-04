from __future__ import annotations

from dataclasses import dataclass

from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession


@dataclass(frozen=True)
class VideoDetails:
    title: str
    description: str | None
    channel_name: str | None


class VideoDetailsCollector:
    def __init__(self, browser: BrowserSession) -> None:
        self.browser = browser

    async def collect(self, canonical_url: str) -> VideoDetails:
        page = self.browser.require_page()
        await page.goto(canonical_url, wait_until="domcontentloaded")
        await self.browser.ensure_safe_page()
        title_locator = page.locator(Selectors.VIDEO_TITLE).first
        await title_locator.wait_for(state="visible")
        title = (await title_locator.inner_text()).strip()
        description_locator = page.locator(Selectors.VIDEO_DESCRIPTION).first
        description = None
        if await description_locator.count():
            description = (await description_locator.inner_text()).strip() or None
        channel_locator = page.locator(Selectors.VIDEO_CHANNEL).first
        channel_name = None
        if await channel_locator.count():
            channel_name = (await channel_locator.inner_text()).strip() or None
        return VideoDetails(title=title, description=description, channel_name=channel_name)
