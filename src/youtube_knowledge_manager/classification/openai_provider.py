import json
from typing import Any

from youtube_knowledge_manager.classification.schemas import (
    CategoryConfig,
    ClassificationInput,
    ProviderResult,
)


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str, *, timeout_seconds: float, max_retries: int) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install the ai extra with: uv sync --extra ai") from exc
        self.model = model
        self._client: Any = OpenAI(timeout=timeout_seconds, max_retries=max_retries)

    def classify(
        self, item: ClassificationInput, categories: list[CategoryConfig]
    ) -> ProviderResult:
        allowed = [
            {"slug": category.slug, "description": category.description}
            for category in categories
            if category.enabled
        ]
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the video into zero or more allowed categories. Return JSON with "
                        "a decisions array. Each item needs category_slug, confidence, is_primary, "
                        "explanation, and identifier='ai'. Do not invent category slugs."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"video": item.model_dump(), "allowed_categories": allowed},
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        raw = response.choices[0].message.content or '{"decisions": []}'
        payload = json.loads(raw)
        usage = None
        if response.usage is not None:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return ProviderResult.model_validate(
            {"decisions": payload.get("decisions", []), "raw_response": raw, "token_usage": usage}
        )
