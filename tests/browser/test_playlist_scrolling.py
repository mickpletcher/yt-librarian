from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from youtube_knowledge_manager.browser.liked_videos import PlaylistVideosCollector


def _raw(video_id: str) -> dict[str, str | None]:
    return {
        "href": f"/watch?v={video_id}&list=PL",
        "title": video_id,
        "channel_name": None,
        "channel_href": None,
        "thumbnail": None,
        "duration": "1:00",
    }


class Items:
    def __init__(self, page: Page, selector: str) -> None:
        self.page = page
        self.selector = selector

    async def evaluate_all(self, *_: object) -> list[dict[str, str | None]]:
        return self.page.batches[min(self.page.index, len(self.page.batches) - 1)]

    async def all_inner_texts(self) -> list[str]:
        return self.page.count_texts if "playlist-byline" in self.selector else []


class Page:
    def __init__(
        self,
        batches: list[list[dict[str, str | None]]],
        count_texts: list[str] | None = None,
    ) -> None:
        self.batches = batches
        self.count_texts = count_texts or []
        self.index = 0

    def locator(self, selector: str) -> Items:
        return Items(self, selector)

    async def evaluate(self, _: str) -> None:
        self.index += 1


class Browser:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.settings = SimpleNamespace(max_scrolls=10, stable_scroll_limit=2)
        self.pause_between_actions = AsyncMock()
        self.ensure_safe_page = AsyncMock()

    def require_page(self) -> Page:
        return self.page


@pytest.mark.browser
@pytest.mark.asyncio
async def test_progressive_scrolling_handles_recycled_nodes() -> None:
    browser = Browser(Page([[_raw("A")], [_raw("B")], [_raw("B")], [_raw("B")]]))
    collector = PlaylistVideosCollector(browser, "PL", expected_video_count=2)  # type: ignore[arg-type]
    collector._open_playlist = AsyncMock()  # type: ignore[method-assign]
    observed: list[str] = []

    async def on_video(video):  # type: ignore[no-untyped-def]
        observed.append(video.youtube_video_id)

    result = await collector.collect(on_video=on_video)

    assert result.complete is True
    assert {video.youtube_video_id for video in result.videos} == {"A", "B"}
    assert observed == ["A", "B"]


@pytest.mark.browser
@pytest.mark.asyncio
async def test_reported_count_mismatch_is_incomplete() -> None:
    browser = Browser(Page([[_raw("A")], [_raw("A")], [_raw("A")]]))
    collector = PlaylistVideosCollector(browser, "PL", expected_video_count=2)  # type: ignore[arg-type]
    collector._open_playlist = AsyncMock()  # type: ignore[method-assign]

    result = await collector.collect()

    assert result.complete is False
    assert result.termination_reason == "reported_count_mismatch"


@pytest.mark.browser
@pytest.mark.asyncio
async def test_missing_reported_count_is_incomplete() -> None:
    browser = Browser(Page([[_raw("A")], [_raw("A")], [_raw("A")]]))
    collector = PlaylistVideosCollector(browser, "PL")  # type: ignore[arg-type]
    collector._open_playlist = AsyncMock()  # type: ignore[method-assign]

    result = await collector.collect()

    assert result.complete is False
    assert result.termination_reason == "reported_count_unavailable"


@pytest.mark.browser
@pytest.mark.asyncio
async def test_playlist_page_count_overrides_stale_card_count() -> None:
    batch = [_raw(str(index)) for index in range(28)]
    browser = Browser(Page([batch, batch, batch], count_texts=["28 videos"]))
    collector = PlaylistVideosCollector(browser, "PL", expected_video_count=15)  # type: ignore[arg-type]
    collector._open_playlist = AsyncMock()  # type: ignore[method-assign]

    result = await collector.collect()

    assert result.complete is True
    assert collector.expected_video_count == 28


@pytest.mark.browser
@pytest.mark.asyncio
async def test_recommendation_links_are_excluded_from_playlist_membership() -> None:
    recommendation = _raw("recommendation")
    recommendation["href"] = "/watch?v=recommendation"
    playlist_item = _raw("member")
    browser = Browser(Page([[playlist_item, recommendation]] * 3, count_texts=["1 video"]))
    collector = PlaylistVideosCollector(browser, "PL")  # type: ignore[arg-type]
    collector._open_playlist = AsyncMock()  # type: ignore[method-assign]

    result = await collector.collect()

    assert result.complete is True
    assert [video.youtube_video_id for video in result.videos] == ["member"]
