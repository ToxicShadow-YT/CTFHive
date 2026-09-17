from __future__ import annotations

from .models import KnowledgeItem


def adjusted_confidence(item: KnowledgeItem) -> float:
    total = item.success_count + item.failure_count
    if not total:
        return item.confidence
    evidence_factor = min(1.0, item.evidence_count / 5)
    outcome_factor = item.success_count / total
    return max(0.0, min(1.0, item.confidence * 0.5 + outcome_factor * 0.5 * evidence_factor))
