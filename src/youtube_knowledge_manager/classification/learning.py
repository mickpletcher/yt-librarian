from collections import Counter

from youtube_knowledge_manager.db.models import VideoCategory


def suggest_category_priorities(manual_assignments: list[VideoCategory]) -> list[tuple[str, int]]:
    counts = Counter(
        assignment.category.slug
        for assignment in manual_assignments
        if assignment.approved is True and assignment.category is not None
    )
    return counts.most_common()
