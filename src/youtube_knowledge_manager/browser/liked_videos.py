from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Locator

from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession

LIKED_VIDEOS_URL = "https://www.youtube.com/playlist?list=LL"


@dataclass(frozen=True)
class CollectedVideo:
    youtube_video_id: str
    canonical_url: str
    title: str
    channel_name: str | None = None
    channel_id: str | None = None
    thumbnail_url: str | None = None
    duration_text: str | None = None
    position: int | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


def extract_video_id(href: str | None) -> str | None:
    if not href:
        return None
    parsed = urlparse(href)
    if parsed.netloc == "youtu.be":
        return parsed.path.strip("/") or None
    video_ids = parse_qs(parsed.query).get("v", [])
    return video_ids[0] if video_ids else None


async def _text(locator: Locator) -> str | None:
    if await locator.count() == 0:
        return None
    value = (await locator.first.inner_text()).strip()
    return value or None


async def _attribute(locator: Locator, name: str) -> str | None:
    if await locator.count() == 0:
        return None
    value = await locator.first.get_attribute(name)
    return value.strip() if value else None


class LikedVideosCollector:
    def __init__(self, browser: BrowserSession) -> None:
        self.browser = browser

    async def collect(
        self, on_video: Callable[[CollectedVideo], Awaitable[None]] | None = None
    ) -> list[CollectedVideo]:
        page = self.browser.require_page()
        await page.goto(LIKED_VIDEOS_URL, wait_until="domcontentloaded")
        await self.browser.ensure_safe_page()
        await page.locator(Selectors.PLAYLIST_ITEMS).first.wait_for(state="attached")

        collected: dict[str, CollectedVideo] = {}
        stable_rounds = 0
        previous_count = -1
        for _ in range(self.browser.settings.max_scrolls):
            items = page.locator(Selectors.PLAYLIST_ITEMS)
            for index in range(await items.count()):
                item = items.nth(index)
                video = await self._parse_item(item, index + 1)
                if video is not None:
                    is_new = video.youtube_video_id not in collected
                    collected[video.youtube_video_id] = video
                    if is_new and on_video is not None:
                        await on_video(video)

            if len(collected) == previous_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
                previous_count = len(collected)
            if stable_rounds >= self.browser.settings.stable_scroll_limit:
                break

            await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            await self.browser.pause_between_actions()
            await self.browser.ensure_safe_page()

        return list(collected.values())

    async def _parse_item(self, item: Locator, position: int) -> CollectedVideo | None:
        link = item.locator(Selectors.VIDEO_LINK)
        href = await _attribute(link, "href")
        youtube_video_id = extract_video_id(href)
        if youtube_video_id is None:
            return None
        title = await _attribute(link, "title") or await _text(link) or "Untitled video"
        channel_link = item.locator(Selectors.CHANNEL_LINK)
        channel_href = await _attribute(channel_link, "href")
        channel_id = channel_href.rstrip("/").split("/")[-1] if channel_href else None
        thumbnail = await _attribute(item.locator(Selectors.THUMBNAIL), "src")
        duration = await _text(item.locator(Selectors.DURATION))
        return CollectedVideo(
            youtube_video_id=youtube_video_id,
            canonical_url=f"https://www.youtube.com/watch?v={youtube_video_id}",
            title=title,
            channel_name=await _text(channel_link),
            channel_id=channel_id,
            thumbnail_url=thumbnail,
            duration_text=duration,
            position=position,
            raw_metadata={"playlist_position": position, "duration_text": duration},
        )
