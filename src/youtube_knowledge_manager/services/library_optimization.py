from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.repositories import (
    ClassificationRepository,
    PlaylistInventoryRow,
    PlaylistRepository,
)


@dataclass(frozen=True)
class LibraryOptimizationSummary:
    playlist_count: int
    system_playlist_count: int
    empty_regular_playlist_count: int
    oversized_playlist_count: int
    active_membership_count: int
    unique_video_count: int
    duplicate_regular_video_count: int
    uncategorized_video_count: int
    recommended_addition_count: int


@dataclass(frozen=True)
class LibraryOptimizationReport:
    summary: LibraryOptimizationSummary
    playlists: list[PlaylistInventoryRow]
    oversized_playlists: list[PlaylistInventoryRow]


class LibraryOptimizationService:
    def __init__(self, session: Session) -> None:
        self.playlists = PlaylistRepository(session)
        self.classifications = ClassificationRepository(session)

    def analyze(self, *, oversized_threshold: int = 500) -> LibraryOptimizationReport:
        inventory = self.playlists.list_inventory()
        oversized = [
            row
            for row in inventory
            if row.playlist.system_kind is None and row.active_video_count > oversized_threshold
        ]
        empty_regular = sum(
            row.playlist.system_kind is None and row.active_video_count == 0 for row in inventory
        )
        recommendation_keys: set[tuple[int, str]] = set()
        for assignment in self.classifications.list_approved():
            category = assignment.category
            target = category.youtube_playlist_id or category.youtube_playlist_name
            if not category.enabled or target is None:
                continue
            if self.playlists.has_active_membership(
                video_id=assignment.video_id,
                youtube_playlist_id=category.youtube_playlist_id,
                playlist_name=category.youtube_playlist_name,
            ):
                continue
            recommendation_keys.add((assignment.video_id, target))

        return LibraryOptimizationReport(
            summary=LibraryOptimizationSummary(
                playlist_count=len(inventory),
                system_playlist_count=sum(
                    row.playlist.system_kind is not None for row in inventory
                ),
                empty_regular_playlist_count=empty_regular,
                oversized_playlist_count=len(oversized),
                active_membership_count=self.playlists.active_membership_count(),
                unique_video_count=self.playlists.active_unique_video_count(),
                duplicate_regular_video_count=self.playlists.duplicate_regular_video_count(),
                uncategorized_video_count=self.playlists.uncategorized_active_video_count(),
                recommended_addition_count=len(recommendation_keys),
            ),
            playlists=inventory,
            oversized_playlists=oversized,
        )
