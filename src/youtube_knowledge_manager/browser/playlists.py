from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from youtube_knowledge_manager.browser.liked_videos import (
    PLAYLIST_LOAD_ATTEMPTS,
    PLAYLIST_LOAD_TIMEOUT_MS,
    parse_reported_video_count,
)
from youtube_knowledge_manager.browser.selectors import Selectors
from youtube_knowledge_manager.browser.session import BrowserSession

PLAYLIST_LIBRARY_URL = "https://www.youtube.com/feed/playlists"
MINIMUM_LIBRARY_OBSERVATION_ROUNDS = 10


class PlaylistLibraryLoadError(RuntimeError):
    pass


@dataclass(frozen=True)
class DiscoveredPlaylist:
    youtube_playlist_id: str
    name: str
    canonical_url: str
    system_kind: str | None = None
    reported_video_count: int | None = None


@dataclass(frozen=True)
class PlaylistLibraryCrawlResult:
    playlists: list[DiscoveredPlaylist]
    complete: bool
    termination_reason: str


def extract_playlist_id(href: str | None) -> str | None:
    if not href:
        return None
    values = parse_qs(urlparse(href).query).get("list", [])
    return values[0] if values else None


def discovered_playlist_from_raw(raw: dict[str, Any]) -> DiscoveredPlaylist | None:
    href = raw.get("href")
    title = raw.get("title")
    metadata = raw.get("metadata")
    if not isinstance(href, str) or not isinstance(title, str):
        return None
    youtube_playlist_id = extract_playlist_id(href)
    name = title.strip()
    if youtube_playlist_id is None or not name:
        return None
    system_kind = {"LL": "liked", "WL": "watch_later"}.get(youtube_playlist_id)
    return DiscoveredPlaylist(
        youtube_playlist_id=youtube_playlist_id,
        name=name,
        canonical_url=f"https://www.youtube.com/playlist?list={youtube_playlist_id}",
        system_kind=system_kind,
        reported_video_count=parse_reported_video_count(
            metadata if isinstance(metadata, str) else None
        ),
    )


class PlaylistLibraryCollector:
    def __init__(self, browser: BrowserSession) -> None:
        self.browser = browser

    async def collect(self) -> PlaylistLibraryCrawlResult:
        page = self.browser.require_page()
        await self._open_library(page)
        collected: dict[str, DiscoveredPlaylist] = {}
        stable_rounds = 0
        previous_count = -1
        termination_reason = "maximum_scrolls_reached"
        for round_index in range(self.browser.settings.max_scrolls):
            raw_cards: list[dict[str, Any]] = await page.locator(
                Selectors.PLAYLIST_CARDS
            ).evaluate_all(
                """
                (elements, selectors) => elements.map(element => {
                    const link = element.querySelector(selectors.link);
                    const title = element.querySelector(selectors.title);
                    const count = element.querySelector(selectors.count);
                    return {
                        href: link?.getAttribute('href') ?? null,
                        title: title?.getAttribute('title') ?? title?.textContent ?? null,
                        metadata: count?.textContent ?? null,
                    };
                })
                """,
                {
                    "link": Selectors.PLAYLIST_CARD_LINK,
                    "title": Selectors.PLAYLIST_CARD_TITLE,
                    "count": Selectors.PLAYLIST_CARD_COUNT,
                },
            )
            for raw_card in raw_cards:
                playlist = discovered_playlist_from_raw(raw_card)
                if playlist is not None:
                    collected[playlist.youtube_playlist_id] = playlist

            if len(collected) == previous_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
                previous_count = len(collected)
            if (
                round_index + 1 >= MINIMUM_LIBRARY_OBSERVATION_ROUNDS
                and stable_rounds >= self.browser.settings.stable_scroll_limit
            ):
                termination_reason = "stable"
                break
            await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            await page.locator(Selectors.LIBRARY_CONTINUATION).evaluate_all(
                "elements => elements.at(-1)?.scrollIntoView({block: 'center'})"
            )
            await self.browser.pause_between_actions()
            await self.browser.ensure_safe_page()
        continuation_remaining = await page.locator(Selectors.LIBRARY_CONTINUATION).count() > 0
        complete = termination_reason == "stable" and not continuation_remaining
        if termination_reason == "stable" and continuation_remaining:
            termination_reason = "continuation_not_exhausted"
        return PlaylistLibraryCrawlResult(
            playlists=list(collected.values()),
            complete=complete,
            termination_reason=termination_reason,
        )

    async def _open_library(self, page: Page) -> None:
        last_error: PlaywrightTimeoutError | None = None
        for attempt in range(1, PLAYLIST_LOAD_ATTEMPTS + 1):
            try:
                await page.goto(PLAYLIST_LIBRARY_URL, wait_until="commit")
                await self.browser.ensure_safe_page()
                await page.locator(Selectors.PLAYLIST_CARD_LINK).first.wait_for(
                    state="attached", timeout=PLAYLIST_LOAD_TIMEOUT_MS
                )
                await self.browser.ensure_safe_page()
                return
            except PlaywrightTimeoutError as error:
                last_error = error
                await self.browser.ensure_safe_page()
                if attempt < PLAYLIST_LOAD_ATTEMPTS:
                    await self.browser.pause_between_actions()
        raise PlaylistLibraryLoadError(
            "The saved-playlists library did not load after three attempts. Close the "
            "dedicated browser completely, verify the Playlists page loads normally, and retry."
        ) from last_error
