from __future__ import annotations

import shutil
import subprocess

from .openai_compatible import ModelResponse


class ClaudeCodeModel:
    """Optional Claude Code CLI adapter; never required for local solver mode."""

    def __init__(self, command: str = "claude"):
        self.command = command

    def available(self) -> bool:
        return shutil.which(self.command) is not None

    def complete(self, prompt: str, system: str = "") -> ModelResponse:
        if not self.available():
            raise ConnectionError("Claude Code CLI is unavailable")
        completed = subprocess.run([self.command, "-p", prompt], capture_output=True, text=True, timeout=120, check=False)
        if completed.returncode:
            raise ConnectionError(completed.stderr.strip() or "Claude Code failed")
        return ModelResponse(completed.stdout, {"adapter": "claude-code", "exit_code": completed.returncode})
