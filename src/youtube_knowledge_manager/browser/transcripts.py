from __future__ import annotations

from dataclasses import dataclass

from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession


@dataclass(frozen=True)
class TranscriptSegment:
    timestamp: str
    text: str


class TranscriptCollector:
    def __init__(self, browser: BrowserSession) -> None:
        self.browser = browser

    async def collect_if_available(self) -> list[TranscriptSegment]:
        page = self.browser.require_page()
        await self.browser.ensure_safe_page()
        more = page.locator(Selectors.MORE_ACTIONS_BUTTON).last
        if await more.count() == 0:
            return []
        await more.click()
        menu_item = page.locator(Selectors.TRANSCRIPT_MENU_ITEM).first
        if await menu_item.count() == 0:
            await page.keyboard.press("Escape")
            return []
        await menu_item.click()
        segments = page.locator(Selectors.TRANSCRIPT_SEGMENT)
        await segments.first.wait_for(state="attached")
        result: list[TranscriptSegment] = []
        for index in range(await segments.count()):
            segment = segments.nth(index)
            timestamp = (await segment.locator(Selectors.TRANSCRIPT_TIME).inner_text()).strip()
            text = (await segment.locator(Selectors.TRANSCRIPT_TEXT).inner_text()).strip()
            if text:
                result.append(TranscriptSegment(timestamp=timestamp, text=text))
        return result
