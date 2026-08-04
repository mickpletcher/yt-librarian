import re
from pathlib import Path
from typing import Any

import yaml

from youtube_knowledge_manager.classification.schemas import (
    ClassificationDecision,
    ClassificationInput,
    RuleConfig,
    RulesConfig,
)


def load_rules(path: Path) -> list[RuleConfig]:
    with path.open(encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    parsed = RulesConfig.model_validate(payload)
    return sorted(
        (rule for rule in parsed.rules if rule.enabled),
        key=lambda item: item.priority,
        reverse=True,
    )


class RulesEngine:
    def __init__(self, rules: list[RuleConfig]) -> None:
        self.rules = sorted(rules, key=lambda item: item.priority, reverse=True)

    def classify(self, item: ClassificationInput) -> list[ClassificationDecision]:
        text = " ".join(
            value for value in [item.title, item.description, item.transcript_text] if value
        ).casefold()
        channel = (item.channel_name or "").casefold()
        decisions: dict[str, ClassificationDecision] = {}
        for rule in self.rules:
            if not self._matches(rule, text=text, channel=channel):
                continue
            for index, slug in enumerate(rule.categories):
                candidate = ClassificationDecision(
                    category_slug=slug,
                    confidence=rule.confidence,
                    is_primary=index == 0,
                    explanation=f"Matched deterministic rule '{rule.name}'",
                    identifier=rule.name,
                )
                current = decisions.get(slug)
                if current is None or candidate.confidence > current.confidence:
                    decisions[slug] = candidate
        return list(decisions.values())

    @staticmethod
    def _matches(rule: RuleConfig, *, text: str, channel: str) -> bool:
        any_keywords = [keyword.casefold() for keyword in rule.any_keywords]
        all_keywords = [keyword.casefold() for keyword in rule.all_keywords]
        channels = [name.casefold() for name in rule.channels]
        checks: list[bool] = []
        if any_keywords:
            checks.append(any(keyword in text for keyword in any_keywords))
        if all_keywords:
            checks.append(all(keyword in text for keyword in all_keywords))
        if rule.regex_patterns:
            checks.append(
                any(re.search(pattern, text, re.IGNORECASE) for pattern in rule.regex_patterns)
            )
        if channels:
            checks.append(channel in channels)
        return bool(checks) and all(checks)
