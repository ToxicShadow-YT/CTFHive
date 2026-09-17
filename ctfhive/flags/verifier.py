from __future__ import annotations

import re

from .detector import FlagCandidate


def validate_flag(candidate: FlagCandidate, patterns: tuple[str, ...]) -> bool:
    return any(re.fullmatch(pattern, candidate.value) for pattern in patterns)


def choose_flag(candidates: list[FlagCandidate], patterns: tuple[str, ...]) -> FlagCandidate | None:
    valid = [candidate for candidate in candidates if validate_flag(candidate, patterns)]
    return max(valid, key=lambda candidate: candidate.confidence, default=None)
