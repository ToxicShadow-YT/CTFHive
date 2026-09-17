from __future__ import annotations

from .models import SourceType, TrustTier


def trust_for_source(source_type: SourceType, url: str | None = None) -> TrustTier:
    if source_type == SourceType.DOCUMENTATION or (url and ("rfc-editor.org" in url or "docs." in url)):
        return TrustTier.OFFICIAL
    if source_type in {SourceType.GITHUB, SourceType.WEB}:
        return TrustTier.COMMUNITY
    if source_type in {SourceType.SOLVED_CHALLENGE, SourceType.USER_WRITEUP}:
        return TrustTier.ESTABLISHED
    return TrustTier.UNKNOWN
