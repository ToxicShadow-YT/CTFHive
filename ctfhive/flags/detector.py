from __future__ import annotations

import re
from dataclasses import dataclass

from ctfhive.evidence.models import Evidence


@dataclass(frozen=True)
class FlagCandidate:
    value: str
    evidence_id: str
    source_tool: str
    confidence: float


def extract_flags(text: str, patterns: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            value = match if isinstance(match, str) else match[0]
            if value not in found:
                found.append(value)
    return found


def candidates_from_evidence(records: list[Evidence], patterns: tuple[str, ...]) -> list[FlagCandidate]:
    candidates: list[FlagCandidate] = []
    for index, record in enumerate(records):
        for flag in extract_flags(record.stdout + "\n" + record.stderr, patterns):
            candidates.append(FlagCandidate(flag, f"{record.timestamp}:{index}", record.tool, record.confidence))
    return candidates
