import json
from urllib.request import Request, urlopen

from youtube_knowledge_manager.classification.schemas import (
    CategoryConfig,
    ClassificationInput,
    ProviderResult,
)


class LocalProvider:
    name = "local"

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def classify(
        self, item: ClassificationInput, categories: list[CategoryConfig]
    ) -> ProviderResult:
        prompt = {
            "video": item.model_dump(),
            "allowed_categories": [
                category.model_dump() for category in categories if category.enabled
            ],
            "required_output": {
                "decisions": [
                    {
                        "category_slug": "allowed slug",
                        "confidence": 0.0,
                        "is_primary": True,
                        "explanation": "short reason",
                        "identifier": "local-ai",
                    }
                ]
            },
        }
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "Return only valid JSON. Use only allowed category slugs.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            }
        ).encode()
        request = Request(  # noqa: S310
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as response:  # noqa: S310
            response_payload = json.loads(response.read())
        raw = response_payload["choices"][0]["message"]["content"]
        parsed = json.loads(raw)
        usage = response_payload.get("usage")
        return ProviderResult.model_validate(
            {"decisions": parsed.get("decisions", []), "raw_response": raw, "token_usage": usage}
        )
