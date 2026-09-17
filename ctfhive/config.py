from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    model: str = "qwen2.5:14b"
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    workspace_root: Path = Path("challenges")
    evidence_root: Path = Path("evidence")
    knowledge_path: Path = Path("knowledge/ctfhive.sqlite3")
    learning_mode: str = "safe"
    tool_timeout: float = 30.0
    stdout_limit: int = 32_000
    stderr_limit: int = 8_000
    wrong_submission_limit: int = 3
    flag_patterns: tuple[str, ...] = (r"FLAG\{[^\r\n}]+\}", r"CTF\{[^\r\n}]+\}", r"flag\{[^\r\n}]+\}")
    ctfd_url: str | None = None
    ctfd_token: str | None = None
    allow_submission: bool = False
    claude_command: str = "claude"

    @classmethod
    def from_env(cls) -> "Config":
        patterns = tuple(p for p in os.getenv("CTFHIVE_FLAG_PATTERNS", "").split(",") if p) or cls.flag_patterns
        return cls(
            model=os.getenv("MODEL", cls.model),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", cls.ollama_base_url).rstrip("/"),
            workspace_root=Path(os.getenv("CTFHIVE_WORKSPACE", str(cls.workspace_root))),
            evidence_root=Path(os.getenv("CTFHIVE_EVIDENCE", str(cls.evidence_root))),
            knowledge_path=Path(os.getenv("CTFHIVE_KNOWLEDGE", str(cls.knowledge_path))),
            learning_mode=os.getenv("CTFHIVE_LEARNING_MODE", cls.learning_mode).lower(),
            tool_timeout=float(os.getenv("CTFHIVE_TOOL_TIMEOUT", cls.tool_timeout)),
            stdout_limit=int(os.getenv("CTFHIVE_STDOUT_LIMIT", cls.stdout_limit)),
            stderr_limit=int(os.getenv("CTFHIVE_STDERR_LIMIT", cls.stderr_limit)),
            wrong_submission_limit=int(os.getenv("CTFHIVE_WRONG_SUBMISSION_LIMIT", cls.wrong_submission_limit)),
            flag_patterns=patterns,
            ctfd_url=os.getenv("CTFD_URL"),
            ctfd_token=os.getenv("CTFD_TOKEN"),
            allow_submission=os.getenv("CTFHIVE_ALLOW_SUBMISSION", "false").lower() == "true",
            claude_command=os.getenv("CLAUDE_COMMAND", cls.claude_command),
        )

    def ensure_dirs(self) -> None:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
