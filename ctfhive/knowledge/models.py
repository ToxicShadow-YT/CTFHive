from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class LearningMode(StrEnum):
    AUTO = "auto"
    SAFE = "safe"
    MANUAL = "manual"


class SourceType(StrEnum):
    SOLVED_CHALLENGE = "solved_challenge"
    FAILED_ATTEMPT = "failed_attempt"
    GITHUB = "github"
    WEB = "web"
    DOCUMENTATION = "documentation"
    LOCAL_NOTE = "local_note"
    USER_WRITEUP = "user_writeup"


class TrustTier(StrEnum):
    OFFICIAL = "tier1"
    ESTABLISHED = "tier2"
    COMMUNITY = "tier3"
    UNKNOWN = "tier4"


@dataclass
class KnowledgeItem:
    title: str
    category: str
    topic: str
    summary: str
    content: str
    source: str
    source_type: SourceType
    url: str | None = None
    challenge: str | None = None
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.5
    source_quality: TrustTier = TrustTier.UNKNOWN
    evidence_count: int = 1
    success_count: int = 0
    failure_count: int = 0
    approved: bool = True
    id: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "category": self.category, "topic": self.topic,
            "summary": self.summary, "content": self.content, "source": self.source,
            "source_type": self.source_type.value, "url": self.url, "challenge": self.challenge,
            "tags": ",".join(self.tags), "confidence": max(0.0, min(1.0, self.confidence)),
            "source_quality": self.source_quality.value, "evidence_count": self.evidence_count,
            "success_count": self.success_count, "failure_count": self.failure_count,
            "approved": int(self.approved), "created_at": self.created_at, "updated_at": self.updated_at,
        }

    @classmethod
    def from_record(cls, row: dict[str, Any]) -> "KnowledgeItem":
        return cls(**{**row, "source_type": SourceType(row["source_type"]), "source_quality": TrustTier(row["source_quality"]), "tags": [tag for tag in row["tags"].split(",") if tag], "approved": bool(row["approved"])})
