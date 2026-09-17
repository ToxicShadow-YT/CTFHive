from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class CTFdClient:
    base_url: str
    token: str
    timeout: float = 10.0

    def _request(self, path: str, method: str = "GET", payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(self.base_url.rstrip("/") + path, data=data, method=method, headers={"Authorization": f"Token {self.token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode())

    def get_challenges(self) -> dict:
        return self._request("/api/v1/challenges")

    def get_challenge(self, challenge_id: int) -> dict:
        return self._request(f"/api/v1/challenges/{challenge_id}")

    def download_artifacts(self, challenge_id: int) -> dict:
        return self.get_challenge(challenge_id)

    def submit_flag(self, flag: str) -> dict:
        return self._request("/api/v1/flags", "POST", {"flag": flag})
