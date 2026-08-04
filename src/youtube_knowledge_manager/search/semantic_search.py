from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticSearchStatus:
    available: bool = False
    reason: str = (
        "Semantic search is not configured. "
        "No transcript data will be sent to an embedding provider."
    )


def get_semantic_search_status() -> SemanticSearchStatus:
    return SemanticSearchStatus()
