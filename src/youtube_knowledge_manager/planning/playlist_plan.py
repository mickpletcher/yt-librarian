from dataclasses import dataclass

from sqlalchemy.orm import Session

from youtube_knowledge_manager.db.models import BrowserAction
from youtube_knowledge_manager.db.repositories import (
    BrowserActionRepository,
    ClassificationRepository,
    PlaylistRepository,
)


@dataclass(frozen=True)
class PlanSummary:
    eligible_assignments: int
    created_actions: int
    existing_actions: int
    skipped_unmapped: int
    already_present: int


class PlaylistPlanner:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.classifications = ClassificationRepository(session)
        self.actions = BrowserActionRepository(session)
        self.playlists = PlaylistRepository(session)

    def generate(self, *, dry_run: bool, persist: bool) -> tuple[PlanSummary, list[BrowserAction]]:
        assignments = self.classifications.list_approved()
        planned: list[BrowserAction] = []
        created = 0
        existing = 0
        skipped = 0
        already_present = 0
        for assignment in assignments:
            category = assignment.category
            if not category.enabled or not (
                category.youtube_playlist_id or category.youtube_playlist_name
            ):
                skipped += 1
                continue
            if self.playlists.has_active_membership(
                video_id=assignment.video_id,
                youtube_playlist_id=category.youtube_playlist_id,
                playlist_name=category.youtube_playlist_name,
            ):
                already_present += 1
                continue
            action, was_created = self.actions.get_or_create_add(
                video=assignment.video, category=category, dry_run=dry_run
            )
            planned.append(action)
            created += int(was_created)
            existing += int(not was_created)
        if persist:
            self.session.commit()
        else:
            self.session.rollback()
        return (
            PlanSummary(
                eligible_assignments=len(assignments),
                created_actions=created,
                existing_actions=existing,
                skipped_unmapped=skipped,
                already_present=already_present,
            ),
            planned,
        )
