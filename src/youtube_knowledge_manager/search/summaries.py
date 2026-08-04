from youtube_knowledge_manager.db.models import Video


def create_local_summary(video: Video, max_characters: int = 400) -> str | None:
    source = video.description
    if not source and video.transcripts:
        source = video.transcripts[0].transcript_text
    if not source:
        return None
    normalized = " ".join(source.split())
    if len(normalized) <= max_characters:
        return normalized
    shortened = normalized[: max_characters - 1].rsplit(" ", 1)[0]
    return f"{shortened}…"
