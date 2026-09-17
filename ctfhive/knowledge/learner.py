from __future__ import annotations

from ctfhive.evidence.models import Evidence

from .models import KnowledgeItem, LearningMode, SourceType, TrustTier
from .store import KnowledgeStore
from .security import safe_knowledge_text


def learn_from_attempt(store: KnowledgeStore, challenge: str, category: str, records: list[Evidence], solved: bool, mode: LearningMode = LearningMode.SAFE, flag: str | None = None) -> int | None:
    if mode == LearningMode.MANUAL:
        return None
    tools = ", ".join(sorted({record.tool for record in records})) or "none"
    failures = [record.tool for record in records if record.exit_code not in (0,)]
    outcome = "successful" if solved else "incomplete"
    summary = f"{category.upper()} challenge analysis was {outcome}; tools used: {tools}."
    content = f"Observed tools: {tools}. Failed actions: {', '.join(failures) or 'none'}. General lesson: use evidence to choose the next hypothesis rather than repeating unsupported actions."
    if category == "rev":
        content += " Locate input validation and comparison functions before attempting full decompilation."
    elif category == "pwn":
        content += " Establish protections and crash control before selecting an exploitation strategy."
    elif category == "crypto":
        content += " Identify encoding, hashing, classical, or modern cryptography before brute force."
    item = KnowledgeItem(f"{category} challenge feedback: {challenge}", category, "strategy feedback", safe_knowledge_text(summary), safe_knowledge_text(content), "local solver evidence", SourceType.SOLVED_CHALLENGE if solved else SourceType.FAILED_ATTEMPT, challenge=challenge, tags=[category, "strategy", outcome], confidence=0.55 if solved else 0.35, source_quality=TrustTier.ESTABLISHED, approved=mode == LearningMode.AUTO or mode == LearningMode.SAFE)
    return store.add(item)
