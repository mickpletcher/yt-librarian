from pathlib import Path


def validate_profile_directory(profile_dir: Path) -> Path:
    resolved = profile_dir.expanduser().resolve()
    risky_names = {"default", "user data", "google", "chrome", "edge"}
    if resolved.name.lower() in risky_names:
        raise ValueError(
            "Use a dedicated YouTube Knowledge Manager browser profile, "
            "not a normal browser profile"
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
