from __future__ import annotations

import re

_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key|token|password|passwd|secret|private[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*[^\s]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
)
_FLAG_PATTERN = re.compile(r"(?i)\b(?:flag|ctf)\{[^\r\n}]+\}")


def redact_secrets(text: str) -> str:
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(lambda match: match.group(1) + "[REDACTED]" if match.lastindex else "[REDACTED]", result)
    return result


def redact_flags(text: str) -> str:
    return _FLAG_PATTERN.sub("[FLAG REDACTED]", text)


def safe_knowledge_text(text: str) -> str:
    return redact_flags(redact_secrets(text))
