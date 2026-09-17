from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Safety(str, Enum):
    READ_ONLY = "read-only"
    LOCAL_MUTATION = "local-mutation"
    NETWORK = "network"
    DANGEROUS = "dangerous"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    category: str
    executable: str
    description: str
    arguments: tuple[str, ...] = ()
    timeout: float = 30.0
    output_limit: int = 32_000
    safety: Safety = Safety.READ_ONLY

    def availability(self) -> str | None:
        import shutil
        return shutil.which(self.executable)

    def command(self, extra_args: list[str]) -> list[str]:
        return [self.executable, *self.arguments, *extra_args]


@dataclass(frozen=True)
class ToolResult:
    command: list[str]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    truncated: bool = False
    cwd: Path | None = None
