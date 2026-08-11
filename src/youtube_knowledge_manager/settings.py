from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="YKM_",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "sqlite:///data/youtube_knowledge_manager.sqlite3"
    browser_profile_dir: Path = Path("data/browser-profile")
    browser_channel: Literal["chromium", "chrome", "msedge"] = "chrome"
    headless: bool = False
    dry_run: bool = True
    allow_playlist_removals: bool = False
    min_action_delay_seconds: float = Field(default=1.5, ge=0.5)
    max_action_delay_seconds: float = Field(default=3.5, ge=0.5)
    max_scrolls: int = Field(default=500, ge=1, le=10_000)
    stable_scroll_limit: int = Field(default=4, ge=2, le=20)
    categories_path: Path = Path("config/categories.yaml")
    rules_path: Path = Path("config/rules.yaml")
    review_confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    ai_provider: Literal["none", "openai", "local"] = "none"
    ai_model: str = "gpt-5-mini"
    ai_base_url: str = "http://localhost:11434/v1"
    ai_prompt_version: str = "v1"
    ai_timeout_seconds: float = Field(default=60.0, ge=5.0, le=300.0)
    ai_max_retries: int = Field(default=2, ge=0, le=5)
    ai_daily_token_limit: int = Field(default=100_000, ge=0)
    ai_input_cost_per_million: float = Field(default=0.0, ge=0.0)
    ai_output_cost_per_million: float = Field(default=0.0, ge=0.0)
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_delays(self) -> "Settings":
        if self.max_action_delay_seconds < self.min_action_delay_seconds:
            raise ValueError("max_action_delay_seconds must be at least min_action_delay_seconds")
        return self

    def prepare_local_directories(self) -> None:
        if self.database_url.startswith("sqlite:///") and ":memory:" not in self.database_url:
            database_path = Path(self.database_url.removeprefix("sqlite:///"))
            database_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
