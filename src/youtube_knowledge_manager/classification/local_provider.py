import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from youtube_knowledge_manager.classification.schemas import (
    CategoryConfig,
    ClassificationInput,
    ProviderResult,
)


class LocalProvider:
    name = "local"

    def __init__(
        self,
        model: str,
        base_url: str,
        *,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise ValueError("Local AI base URL must use HTTP(S) on the loopback interface")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

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
        response_payload = None
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(  # noqa: S310  # nosec B310
                    request, timeout=self.timeout_seconds
                ) as response:
                    response_payload = json.loads(response.read())
                break
            except (HTTPError, URLError, TimeoutError):
                if attempt >= self.max_retries:
                    raise
                time.sleep(min(2**attempt, 4))
        if response_payload is None:
            raise RuntimeError("Local AI provider returned no response")
        raw = response_payload["choices"][0]["message"]["content"]
        parsed = json.loads(raw)
        usage = response_payload.get("usage")
        return ProviderResult.model_validate(
            {"decisions": parsed.get("decisions", []), "raw_response": raw, "token_usage": usage}
        )
