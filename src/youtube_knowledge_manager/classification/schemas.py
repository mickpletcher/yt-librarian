from pydantic import BaseModel, ConfigDict, Field


class CategoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    slug: str
    description: str | None = None
    parent_slug: str | None = None
    youtube_playlist_name: str | None = None
    youtube_playlist_id: str | None = None
    enabled: bool = True
    system_managed: bool = False


class CategoriesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[CategoryConfig]


class RuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    priority: int = 0
    enabled: bool = True
    any_keywords: list[str] = Field(default_factory=list)
    all_keywords: list[str] = Field(default_factory=list)
    regex_patterns: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    categories: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class RulesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[RuleConfig]


class ClassificationInput(BaseModel):
    youtube_video_id: str
    title: str
    description: str | None = None
    channel_name: str | None = None
    transcript_text: str | None = None


class ClassificationDecision(BaseModel):
    category_slug: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_primary: bool = False
    explanation: str
    identifier: str


class ProviderResult(BaseModel):
    decisions: list[ClassificationDecision]
    raw_response: str
    token_usage: dict[str, int] | None = None
