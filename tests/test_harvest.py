from __future__ import annotations

import base64
import json
from pathlib import Path

from ctfhive.knowledge.harvest import harvest_github
from ctfhive.knowledge.store import KnowledgeStore


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return self.payload


def test_github_harvest_is_bounded_and_redacts(monkeypatch, tmp_path: Path):
    readme = base64.b64encode(b"Reverse engineering PIE binaries. FLAG{do-not-store}").decode()

    def fake_urlopen(request, timeout):
        url = request.full_url
        if "/readme" in url:
            return FakeResponse({"content": readme})
        return FakeResponse({"items": [{"full_name": "example/writeup", "description": "CTF reverse engineering", "html_url": "https://github.com/example/writeup"}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    learned = harvest_github("ctf writeup", store, limit=100)
    assert len(learned) == 1
    item = store.get(learned[0].id)
    assert item is not None
    assert item.category == "rev"
    assert "FLAG{" not in item.content
