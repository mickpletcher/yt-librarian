from typing import Protocol

from youtube_knowledge_manager.classification.schemas import (
    CategoryConfig,
    ClassificationInput,
    ProviderResult,
)


class AIProvider(Protocol):
    name: str
    model: str

    def classify(
        self, item: ClassificationInput, categories: list[CategoryConfig]
    ) -> ProviderResult: ...
