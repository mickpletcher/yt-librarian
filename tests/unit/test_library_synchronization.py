import pytest
from sqlalchemy.orm import Session

import youtube_knowledge_manager.collection.library_synchronization as synchronization
from youtube_knowledge_manager.browser.liked_videos import PlaylistCrawlResult
from youtube_knowledge_manager.browser.playlists import (
    DiscoveredPlaylist,
    PlaylistLibraryCrawlResult,
)
from youtube_knowledge_manager.collection.library_synchronization import (
    IncompletePlaylistLibraryError,
    LibrarySynchronizationService,
    select_limited_playlists,
)
from youtube_knowledge_manager.db.repositories import (
    PlaylistRepository,
    PlaylistUpsert,
    VideoRepository,
    VideoUpsert,
)
from youtube_knowledge_manager.settings import Settings


def _playlist(
    youtube_id: str,
    name: str,
    count: int | None,
    system_kind: str | None = None,
) -> DiscoveredPlaylist:
    return DiscoveredPlaylist(
        youtube_playlist_id=youtube_id,
        name=name,
        canonical_url=f"https://www.youtube.com/playlist?list={youtube_id}",
        system_kind=system_kind,
        reported_video_count=count,
    )


def test_limited_library_preview_prefers_small_known_regular_playlists() -> None:
    playlists = [
        _playlist("LL", "Liked videos", 3_000, "liked"),
        _playlist("UNKNOWN", "Unknown", None),
        _playlist("LARGE", "Large", 900),
        _playlist("EMPTY", "Empty", 0),
        _playlist("SMALL", "Small", 4),
    ]

    selected = select_limited_playlists(playlists, 3)

    assert [playlist.youtube_playlist_id for playlist in selected] == [
        "EMPTY",
        "SMALL",
        "LARGE",
    ]


def test_unlimited_library_sync_preserves_discovery_order() -> None:
    playlists = [
        _playlist("SECOND", "Second", 2),
        _playlist("FIRST", "First", 1),
    ]

    assert select_limited_playlists(playlists, None) is playlists


@pytest.mark.asyncio
async def test_empty_playlist_deactivates_previous_memberships(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    playlist_repository = PlaylistRepository(db_session)
    playlist = playlist_repository.upsert(
        PlaylistUpsert(
            youtube_playlist_id="EMPTY",
            name="Empty",
            canonical_url="https://www.youtube.com/playlist?list=EMPTY",
        )
    ).playlist
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="video",
                canonical_url="https://www.youtube.com/watch?v=video",
                title="video",
                content_fingerprint="0" * 64,
            )
        )
        .video
    )
    membership, _ = playlist_repository.upsert_membership(
        playlist=playlist,
        video=video,
        position=1,
    )
    db_session.commit()

    class FakeBrowserSession:
        def __init__(self, _: Settings) -> None:
            pass

        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            pass

    class FakePlaylistLibraryCollector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self) -> PlaylistLibraryCrawlResult:
            return PlaylistLibraryCrawlResult(
                playlists=[_playlist("EMPTY", "Empty", 0)],
                complete=True,
                termination_reason="stable",
            )

    class FakePlaylistVideosCollector:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def collect(self, **_: object) -> PlaylistCrawlResult:
            return PlaylistCrawlResult(videos=[], complete=True, termination_reason="stable")

    monkeypatch.setattr(synchronization, "BrowserSession", FakeBrowserSession)
    monkeypatch.setattr(
        synchronization,
        "PlaylistLibraryCollector",
        FakePlaylistLibraryCollector,
    )
    monkeypatch.setattr(
        synchronization,
        "PlaylistVideosCollector",
        FakePlaylistVideosCollector,
    )

    summary = await LibrarySynchronizationService(Settings(), db_session).run(
        dry_run=False,
        expected_playlist_count=1,
    )

    db_session.refresh(membership)
    assert summary.memberships_deactivated == 1
    assert membership.active is False


@pytest.mark.asyncio
async def test_incomplete_playlist_preserves_previous_memberships(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    playlists = PlaylistRepository(db_session)
    playlist = playlists.upsert(
        PlaylistUpsert(
            youtube_playlist_id="PARTIAL",
            name="Partial",
            canonical_url="https://www.youtube.com/playlist?list=PARTIAL",
        )
    ).playlist
    video = (
        VideoRepository(db_session)
        .upsert(
            VideoUpsert(
                youtube_video_id="existing",
                canonical_url="https://www.youtube.com/watch?v=existing",
                title="Existing",
                content_fingerprint="1" * 64,
            )
        )
        .video
    )
    membership, _ = playlists.upsert_membership(playlist=playlist, video=video, position=1)
    db_session.commit()

    class FakeBrowserSession:
        def __init__(self, _: Settings) -> None:
            pass

        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            pass

    class FakePlaylistLibraryCollector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self) -> PlaylistLibraryCrawlResult:
            return PlaylistLibraryCrawlResult(
                playlists=[_playlist("PARTIAL", "Partial", 2)],
                complete=True,
                termination_reason="stable",
            )

    class FakePlaylistVideosCollector:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def collect(self, **_: object) -> PlaylistCrawlResult:
            return PlaylistCrawlResult(
                videos=[],
                complete=False,
                termination_reason="reported_count_mismatch",
            )

    monkeypatch.setattr(synchronization, "BrowserSession", FakeBrowserSession)
    monkeypatch.setattr(
        synchronization,
        "PlaylistLibraryCollector",
        FakePlaylistLibraryCollector,
    )
    monkeypatch.setattr(
        synchronization,
        "PlaylistVideosCollector",
        FakePlaylistVideosCollector,
    )

    summary = await LibrarySynchronizationService(Settings(), db_session).run(
        dry_run=False,
        expected_playlist_count=1,
    )

    db_session.refresh(membership)
    assert summary.playlists_failed == 1
    assert summary.memberships_deactivated == 0
    assert membership.active is True


@pytest.mark.asyncio
async def test_full_library_sync_rejects_incomplete_discovery(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeBrowserSession:
        def __init__(self, _: Settings) -> None:
            pass

        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            pass

    class FakePlaylistLibraryCollector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self) -> PlaylistLibraryCrawlResult:
            return PlaylistLibraryCrawlResult(
                playlists=[_playlist("VISIBLE", "Visible", 1)],
                complete=False,
                termination_reason="continuation_not_exhausted",
            )

    monkeypatch.setattr(synchronization, "BrowserSession", FakeBrowserSession)
    monkeypatch.setattr(
        synchronization,
        "PlaylistLibraryCollector",
        FakePlaylistLibraryCollector,
    )

    with pytest.raises(IncompletePlaylistLibraryError, match="stopped incomplete"):
        await LibrarySynchronizationService(Settings(), db_session).run(dry_run=True)


@pytest.mark.asyncio
async def test_full_write_requires_expected_playlist_count(db_session: Session) -> None:
    with pytest.raises(ValueError, match="requires an explicit expected playlist count"):
        await LibrarySynchronizationService(Settings(), db_session).run(dry_run=False)


@pytest.mark.asyncio
async def test_expected_playlist_count_mismatch_stops_before_playlist_processing(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    playlist_collector_started = False

    class FakeBrowserSession:
        def __init__(self, _: Settings) -> None:
            pass

        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *args: object) -> None:
            pass

    class FakePlaylistLibraryCollector:
        def __init__(self, _: object) -> None:
            pass

        async def collect(self) -> PlaylistLibraryCrawlResult:
            return PlaylistLibraryCrawlResult(
                playlists=[_playlist("ONLY", "Only", 1)],
                complete=True,
                termination_reason="stable",
            )

    class FakePlaylistVideosCollector:
        def __init__(self, *_: object, **__: object) -> None:
            nonlocal playlist_collector_started
            playlist_collector_started = True

    monkeypatch.setattr(synchronization, "BrowserSession", FakeBrowserSession)
    monkeypatch.setattr(
        synchronization,
        "PlaylistLibraryCollector",
        FakePlaylistLibraryCollector,
    )
    monkeypatch.setattr(
        synchronization,
        "PlaylistVideosCollector",
        FakePlaylistVideosCollector,
    )

    with pytest.raises(IncompletePlaylistLibraryError, match="Expected 2 saved playlists"):
        await LibrarySynchronizationService(Settings(), db_session).run(
            dry_run=False,
            expected_playlist_count=2,
        )

    assert playlist_collector_started is False
