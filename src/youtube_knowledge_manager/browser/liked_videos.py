from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession

LIKED_VIDEOS_URL = "https://www.youtube.com/playlist?list=LL"
PLAYLIST_LOAD_ATTEMPTS = 3
PLAYLIST_LOAD_TIMEOUT_MS = 60_000


class PlaylistLoadError(RuntimeError):
    pass


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


@dataclass(frozen=True)
class PlaylistCrawlResult:
    videos: list[CollectedVideo]
    complete: bool
    termination_reason: str


def extract_video_id(href: str | None) -> str | None:
    if not href:
        return None
    parsed = urlparse(href)
    if parsed.netloc == "youtu.be":
        return parsed.path.strip("/") or None
    video_ids = parse_qs(parsed.query).get("v", [])
    if video_ids:
        return video_ids[0]
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "live"}:
        return path_parts[1]
    return None


def video_href_matches_playlist(href: str | None, youtube_playlist_id: str) -> bool:
    if not href:
        return False
    return youtube_playlist_id in parse_qs(urlparse(href).query).get("list", [])


def parse_reported_video_count(value: str | None) -> int | None:
    if not value:
        return None
    if re.search(r"\bno videos\b", value, flags=re.IGNORECASE):
        return 0
    match = re.search(r"([\d,]+)\s+videos?\b", value, flags=re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else None


def _string_value(raw: dict[str, Any], name: str) -> str | None:
    value = raw.get(name)
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def collected_video_from_raw_item(raw: dict[str, Any], position: int) -> CollectedVideo | None:
    href = _string_value(raw, "href")
    youtube_video_id = extract_video_id(href)
    if youtube_video_id is None:
        return None
    channel_href = _string_value(raw, "channel_href")
    channel_id = channel_href.rstrip("/").split("/")[-1] if channel_href else None
    duration = _string_value(raw, "duration")
    return CollectedVideo(
        youtube_video_id=youtube_video_id,
        canonical_url=f"https://www.youtube.com/watch?v={youtube_video_id}",
        title=_string_value(raw, "title") or "Untitled video",
        channel_name=_string_value(raw, "channel_name"),
        channel_id=channel_id,
        thumbnail_url=_string_value(raw, "thumbnail"),
        duration_text=duration,
        position=position,
        raw_metadata={"playlist_position": position, "duration_text": duration},
    )


class PlaylistVideosCollector:
    def __init__(
        self,
        browser: BrowserSession,
        youtube_playlist_id: str,
        *,
        expected_video_count: int | None = None,
        require_reported_count: bool = False,
    ) -> None:
        self.browser = browser
        self.youtube_playlist_id = youtube_playlist_id
        self.expected_video_count = expected_video_count
        self.require_reported_count = require_reported_count

    @property
    def playlist_url(self) -> str:
        return f"https://www.youtube.com/playlist?list={self.youtube_playlist_id}"

    async def collect(
        self, on_video: Callable[[CollectedVideo], Awaitable[None]] | None = None
    ) -> PlaylistCrawlResult:
        page = self.browser.require_page()
        await self._open_playlist(page)
        count_texts = await page.locator(Selectors.PLAYLIST_VIDEO_COUNT).all_inner_texts()
        page_reported_count = next(
            (
                parsed
                for text in count_texts
                if (parsed := parse_reported_video_count(text)) is not None
            ),
            None,
        )
        if page_reported_count is not None:
            self.expected_video_count = page_reported_count
        elif self.require_reported_count:
            self.expected_video_count = None

        collected: dict[str, CollectedVideo] = {}
        stable_rounds = 0
        previous_count = -1
        termination_reason = "maximum_scrolls_reached"
        for _ in range(self.browser.settings.max_scrolls):
            items = page.locator(Selectors.PLAYLIST_ITEMS)
            raw_items: list[dict[str, Any]] = await items.evaluate_all(
                """
                (elements, selectors) => elements.map(element => {
                    const link = element.querySelector(selectors.videoLink);
                    const title = element.querySelector(selectors.title);
                    const channel = element.querySelector(selectors.channel);
                    const thumbnail = element.querySelector(selectors.thumbnail);
                    const duration = element.querySelector(selectors.duration);
                    return {
                        href: link?.getAttribute('href') ?? null,
                        title: title?.getAttribute('title') ?? title?.textContent ?? null,
                        channel_name: channel?.textContent ?? null,
                        channel_href: channel?.getAttribute('href') ?? null,
                        thumbnail: thumbnail?.getAttribute('src') ?? null,
                        duration: duration?.textContent ?? null,
                    };
                })
                """,
                {
                    "videoLink": Selectors.VIDEO_LINK,
                    "title": Selectors.PLAYLIST_TITLE,
                    "channel": Selectors.CHANNEL_LINK,
                    "thumbnail": Selectors.THUMBNAIL,
                    "duration": Selectors.DURATION,
                },
            )
            for index, raw_item in enumerate(raw_items):
                if not video_href_matches_playlist(
                    _string_value(raw_item, "href"), self.youtube_playlist_id
                ):
                    continue
                video = collected_video_from_raw_item(raw_item, index + 1)
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
                termination_reason = "stable"
                break

            await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            await page.locator(Selectors.PLAYLIST_CONTINUATION).evaluate_all(
                "elements => elements.at(-1)?.scrollIntoView({block: 'center'})"
            )
            await self.browser.pause_between_actions()
            await self.browser.ensure_safe_page()

        complete = (
            termination_reason == "stable"
            and self.expected_video_count is not None
            and len(collected) == self.expected_video_count
        )
        if termination_reason == "stable" and not complete:
            termination_reason = (
                "reported_count_unavailable"
                if self.expected_video_count is None
                else "reported_count_mismatch"
            )
        return PlaylistCrawlResult(
            videos=list(collected.values()),
            complete=complete,
            termination_reason=termination_reason,
        )

    async def _open_playlist(self, page: Page) -> None:
        last_error: PlaywrightTimeoutError | None = None
        for attempt in range(1, PLAYLIST_LOAD_ATTEMPTS + 1):
            try:
                await page.goto(self.playlist_url, wait_until="commit")
                await self.browser.ensure_safe_page()
                await page.locator(
                    f"{Selectors.PLAYLIST_ITEMS}, {Selectors.PLAYLIST_EMPTY_STATE}"
                ).first.wait_for(state="attached", timeout=PLAYLIST_LOAD_TIMEOUT_MS)
                await self.browser.ensure_safe_page()
                return
            except PlaywrightTimeoutError as error:
                last_error = error
                await self.browser.ensure_safe_page()
                if attempt < PLAYLIST_LOAD_ATTEMPTS:
                    await self.browser.pause_between_actions()
        raise PlaylistLoadError(
            "The saved playlist did not load after three attempts. The browser did not show a "
            "recognized login or security prompt. Close the dedicated browser completely, "
            "check that YouTube loads normally, and retry."
        ) from last_error


class LikedVideosCollector(PlaylistVideosCollector):
    def __init__(self, browser: BrowserSession) -> None:
        super().__init__(browser, "LL", require_reported_count=True)
