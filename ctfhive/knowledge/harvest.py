from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from .models import KnowledgeItem, SourceType, TrustTier
from .security import safe_knowledge_text
from .store import KnowledgeStore


_MAX_LIMIT = 20


def _request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ctfhive-knowledge-harvester"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _readme(full_name: str) -> str:
    try:
        payload = _request_json(f"https://api.github.com/repos/{full_name}/readme")
        encoded = payload.get("content", "")
        return base64.b64decode(encoded).decode("utf-8", errors="replace") if encoded else ""
    except (OSError, ValueError, json.JSONDecodeError):
        return ""


def _category(text: str) -> str:
    lowered = text.lower()
    terms = {
        "web": ("web", "http", "sql", "xss"), "pwn": ("pwn", "buffer overflow", "rop"),
        "rev": ("reverse engineering", "binary", "assembly", "ghidra"), "crypto": ("crypto", "rsa", "xor"),
        "forensics": ("forensics", "pcap", "memory dump"), "stego": ("steganography", "zsteg", "lsb"),
        "osint": ("osint", "open source intelligence"),
    }
    return max(terms, key=lambda category: sum(lowered.count(term) for term in terms[category])) if any(term in lowered for values in terms.values() for term in values) else "misc"


def harvest_github(query: str, store: KnowledgeStore, limit: int = 5) -> list[KnowledgeItem]:
    bounded_limit = max(1, min(limit, _MAX_LIMIT))
    search_url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": query, "per_page": bounded_limit})
    payload = _request_json(search_url)
    learned: list[KnowledgeItem] = []
    for repository in payload.get("items", [])[:bounded_limit]:
        name = repository.get("full_name", "unknown")
        description = repository.get("description") or ""
        readme = _readme(name)[:12_000]
        content = safe_knowledge_text(f"{description}\n\n{readme}")
        if not content.strip():
            continue
        category = _category(content)
        item = KnowledgeItem(
            title=name,
            category=category,
            topic="public GitHub CTF/security research",
            summary=safe_knowledge_text(description)[:280] or content[:280],
            content=content,
            source="GitHub public API",
            source_type=SourceType.GITHUB,
            url=repository.get("html_url"),
            tags=["github", "harvested", category],
            confidence=0.3,
            source_quality=TrustTier.COMMUNITY,
        )
        store.add(item, redact=False)
        learned.append(item)
    return learned
