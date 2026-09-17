from __future__ import annotations

from pathlib import Path

from .models import KnowledgeItem, SourceType, TrustTier
from .security import safe_knowledge_text
from .store import KnowledgeStore


def infer_category(text: str) -> str:
    lowered = text.lower()
    scores = {"web": ("http", "web", "sql"), "pwn": ("buffer", "rop", "gadget"), "rev": ("reverse", "binary", "assembly", "pie"), "crypto": ("rsa", "xor", "cipher", "nonce"), "forensics": ("pcap", "memory", "carving"), "stego": ("lsb", "steg", "image"), "osint": ("username", "domain", "osint")}
    return max(scores, key=lambda category: sum(lowered.count(term) for term in scores[category])) if any(term in lowered for terms in scores.values() for term in terms) else "misc"


def import_text(store: KnowledgeStore, path: Path, source_type: SourceType = SourceType.LOCAL_NOTE, approved: bool = True) -> int:
    content = safe_knowledge_text(path.read_text(encoding="utf-8", errors="replace"))
    item = KnowledgeItem(path.stem, infer_category(content), "imported notes", content[:280], content, str(path), source_type, tags=[path.suffix.lstrip(".") or "text"], source_quality=TrustTier.UNKNOWN, approved=approved)
    return store.add(item, redact=False)
