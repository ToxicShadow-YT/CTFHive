from __future__ import annotations

import json
from pathlib import Path

from .security import safe_knowledge_text
from .store import KnowledgeStore


def build_training_examples(store: KnowledgeStore, limit: int = 10000) -> list[dict[str, str]]:
    examples: list[dict[str, str]] = []
    for item in store.search("", limit=limit, include_unapproved=False):
        instruction = safe_knowledge_text(f"Develop a generalized {item.category} CTF analysis strategy for {item.topic}. Do not reveal secrets or challenge flags.")
        response = safe_knowledge_text(f"{item.summary}\n\n{item.content}")
        if "[FLAG REDACTED]" in instruction or "[FLAG REDACTED]" in response:
            response = response.replace("[FLAG REDACTED]", "[generalized result omitted]")
        examples.append({"instruction": instruction, "response": response, "category": item.category, "source": item.source})
    return examples


def export_training_data(store: KnowledgeStore, path: Path, limit: int = 10000) -> int:
    examples = build_training_examples(store, limit)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for example in examples:
            stream.write(json.dumps(example, sort_keys=True) + "\n")
    return len(examples)


def training_status() -> dict[str, str | bool]:
    try:
        import torch  # type: ignore
        return {"available": True, "backend": "torch", "detail": f"torch {torch.__version__} detected; configure a Qwen fine-tuning runner separately"}
    except ImportError:
        return {"available": False, "backend": "none", "detail": "install an approved local Qwen fine-tuning stack before training weights"}
