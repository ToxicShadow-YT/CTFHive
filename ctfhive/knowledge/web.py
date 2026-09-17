from __future__ import annotations

import urllib.parse
import urllib.request

from .models import KnowledgeItem, SourceType, TrustTier
from .security import safe_knowledge_text
from .store import KnowledgeStore


def research_web(query: str, store: KnowledgeStore | None = None) -> list[dict[str, str]]:
    url = "https://www.google.com/search?" + urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(url, headers={"User-Agent": "ctfhive authorized research"})
    with urllib.request.urlopen(request, timeout=10) as response:
        content = response.read().decode("utf-8", errors="replace")
    excerpt = safe_knowledge_text(content[:2000])
    result = {"query": query, "source": url, "summary": excerpt, "confidence": "0.2"}
    if store:
        store.add(KnowledgeItem(f"Web research: {query}", "misc", "targeted web research", excerpt[:280], excerpt, "Google results", SourceType.WEB, url=url, tags=["web", "research"], confidence=0.2, source_quality=TrustTier.UNKNOWN))
    return [result]
