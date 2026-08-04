from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from youtube_knowledge_manager.classification.schemas import CategoriesConfig, CategoryConfig
from youtube_knowledge_manager.db.models import Category
from youtube_knowledge_manager.db.repositories import CategoryRepository


def load_categories(path: Path) -> list[CategoryConfig]:
    with path.open(encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    return CategoriesConfig.model_validate(payload).categories


class CategoryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = CategoryRepository(session)

    def synchronize(self, path: Path) -> list[Category]:
        configs = load_categories(path)
        by_slug: dict[str, Category] = {}
        for config in configs:
            if config.parent_slug is not None:
                continue
            by_slug[config.slug] = self._upsert(config, parent_id=None)
        for config in configs:
            if config.parent_slug is None:
                continue
            parent = by_slug.get(config.parent_slug) or self.repository.get_by_slug(
                config.parent_slug
            )
            if parent is None:
                raise ValueError(
                    f"Category {config.slug} references missing parent {config.parent_slug}"
                )
            by_slug[config.slug] = self._upsert(config, parent_id=parent.id)
        self.session.commit()
        return list(by_slug.values())

    def list_enabled(self) -> list[Category]:
        return self.repository.list_enabled()

    def _upsert(self, config: CategoryConfig, parent_id: int | None) -> Category:
        return self.repository.upsert(
            name=config.name,
            slug=config.slug,
            description=config.description,
            youtube_playlist_name=config.youtube_playlist_name,
            youtube_playlist_id=config.youtube_playlist_id,
            parent_id=parent_id,
            enabled=config.enabled,
            system_managed=config.system_managed,
        )
