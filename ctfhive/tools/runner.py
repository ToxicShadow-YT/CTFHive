from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .base import ToolResult, ToolSpec


class ToolRunner:
    def __init__(self, workspace: Path, stdout_limit: int = 32_000, stderr_limit: int = 8_000):
        self.workspace = workspace.resolve()
        self.stdout_limit = stdout_limit
        self.stderr_limit = stderr_limit

    def run(self, tool: ToolSpec, args: list[str], timeout: float | None = None) -> ToolResult:
        command = tool.command(args)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command, cwd=self.workspace, env={"PATH": os.environ.get("PATH", "")},
                capture_output=True, text=True, timeout=timeout or tool.timeout,
                shell=False, check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            truncated = len(stdout) > self.stdout_limit or len(stderr) > self.stderr_limit
            return ToolResult(command, completed.returncode, stdout[:self.stdout_limit], stderr[:self.stderr_limit], int((time.monotonic() - started) * 1000), False, truncated, self.workspace)
        except subprocess.TimeoutExpired as error:
            stdout = (error.stdout or "") if isinstance(error.stdout, str) else ""
            stderr = (error.stderr or "") if isinstance(error.stderr, str) else ""
            return ToolResult(command, None, stdout[:self.stdout_limit], stderr[:self.stderr_limit], int((time.monotonic() - started) * 1000), True, True, self.workspace)
        except OSError as error:
            return ToolResult(command, None, "", str(error), int((time.monotonic() - started) * 1000), False, False, self.workspace)
