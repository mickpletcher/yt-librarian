from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from youtube_knowledge_manager.classification.ai_provider import AIProvider
from youtube_knowledge_manager.classification.rules import RulesEngine
from youtube_knowledge_manager.classification.schemas import (
    CategoryConfig,
    ClassificationDecision,
    ClassificationInput,
)
from youtube_knowledge_manager.db.base import utc_now


@dataclass(frozen=True)
class ClassificationOutcome:
    decisions: list[ClassificationDecision]
    provider: str
    model: str | None = None
    raw_response: str | None = None
    token_usage: dict[str, int] | None = None
    input_hash: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class ClassificationEngine:
    def __init__(
        self,
        rules_engine: RulesEngine,
        categories: list[CategoryConfig],
        ai_provider: AIProvider | None = None,
    ) -> None:
        self.rules_engine = rules_engine
        self.categories = categories
        self.ai_provider = ai_provider

    def classify(self, item: ClassificationInput) -> ClassificationOutcome:
        input_hash = hashlib.sha256(
            json.dumps(item.model_dump(), sort_keys=True).encode("utf-8")
        ).hexdigest()
        rule_decisions = self.rules_engine.classify(item)
        if rule_decisions:
            return ClassificationOutcome(
                decisions=rule_decisions,
                provider="rules",
                input_hash=input_hash,
                completed_at=utc_now(),
            )
        if self.ai_provider is None:
            return ClassificationOutcome(
                decisions=[], provider="none", input_hash=input_hash, completed_at=utc_now()
            )

        started_at = utc_now()
        try:
            result = self.ai_provider.classify(item, self.categories)
            allowed = {category.slug for category in self.categories if category.enabled}
            decisions = [
                decision for decision in result.decisions if decision.category_slug in allowed
            ]
            return ClassificationOutcome(
                decisions=decisions,
                provider=self.ai_provider.name,
                model=self.ai_provider.model,
                raw_response=result.raw_response,
                token_usage=result.token_usage,
                input_hash=input_hash,
                started_at=started_at,
                completed_at=utc_now(),
            )
        except Exception as exc:
            return ClassificationOutcome(
                decisions=[],
                provider=self.ai_provider.name,
                model=self.ai_provider.model,
                input_hash=input_hash,
                started_at=started_at,
                completed_at=utc_now(),
                error=str(exc),
            )
