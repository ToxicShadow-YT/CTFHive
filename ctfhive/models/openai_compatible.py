from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResponse:
    text: str
    raw: dict


class OpenAICompatibleModel:
    def __init__(self, base_url: str, model: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str, system: str = "") -> ModelResponse:
        payload = json.dumps({"model": self.model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": 0}).encode()
        request = urllib.request.Request(self.base_url + "/chat/completions", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ConnectionError(f"model request failed: {error}") from error
        text = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResponse(text, raw)

    def health(self) -> tuple[bool, str]:
        try:
            request = urllib.request.Request(self.base_url.rsplit("/v1", 1)[0] + "/api/tags")
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status == 200, "reachable"
        except (urllib.error.URLError, TimeoutError) as error:
            return False, str(error)
