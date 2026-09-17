from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .models import KnowledgeItem, SourceType, TrustTier
from .security import safe_knowledge_text
from .store import KnowledgeStore


def search_repositories(query: str, store: KnowledgeStore | None = None, limit: int = 5) -> list[dict]:
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": query, "per_page": limit})
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ctfhive"})
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode())
    results = [{"name": item.get("full_name", ""), "description": item.get("description") or "", "url": item.get("html_url", "")} for item in payload.get("items", [])]
    if store:
        for result in results:
            store.add(KnowledgeItem(result["name"], "misc", "github research", safe_knowledge_text(result["description"]), safe_knowledge_text(result["description"]), "GitHub", SourceType.GITHUB, url=result["url"], tags=["github", "research"], confidence=0.35, source_quality=TrustTier.COMMUNITY))
    return results
