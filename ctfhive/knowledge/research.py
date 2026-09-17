from __future__ import annotations

from .github import search_repositories
from .models import KnowledgeItem
from .store import KnowledgeStore
from .web import research_web


def format_items(items: list[KnowledgeItem]) -> str:
    return "\n\n".join(f"[{item.category}] {item.title} (confidence={item.confidence:.2f}, source={item.source})\n{item.summary}" for item in items)


def retrieve_for_challenge(store: KnowledgeStore, category: str, evidence: str = "", limit: int = 5) -> list[KnowledgeItem]:
    return store.search(f"{category} {evidence}", category=category, limit=limit)

__all__ = ["search_repositories", "research_web", "retrieve_for_challenge", "format_items"]
