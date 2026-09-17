from __future__ import annotations

import os
import platform
import shutil
import sys
import subprocess
from dataclasses import dataclass

from ctfhive.config import Config
from ctfhive.models.ollama import OllamaModel
from ctfhive.tools.registry import ToolRegistry
from ctfhive.tools.agents import agent_status


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def run_checks(config: Config) -> list[Check]:
    if platform.system() == "Linux":
        wsl_detail = "native Linux"
    elif shutil.which("wsl"):
        try:
            result = subprocess.run(["wsl.exe", "--list", "--quiet"], capture_output=True, text=True, timeout=5, check=False)
            distributions = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            wsl_detail = f"installed: {', '.join(distributions)}" if distributions else "WSL installed; no distribution"
        except (OSError, subprocess.SubprocessError):
            wsl_detail = "WSL command unavailable"
    else:
        wsl_detail = "unavailable"
    checks = [Check("Python", "REQUIRED", platform.python_version()), Check("WSL/Linux runtime", "OPTIONAL", wsl_detail), Check("Docker", "OPTIONAL", shutil.which("docker") or "unavailable")]
    healthy, detail = OllamaModel(config.ollama_base_url, config.model).health()
    checks.append(Check("Ollama connectivity", "REQUIRED" if healthy else "UNAVAILABLE", detail))
    checks.append(Check("Configured model", "REQUIRED", config.model))
    for tool, path in ToolRegistry().status():
        checks.append(Check(f"tool:{tool.name}", "AVAILABLE" if path else "OPTIONAL", path or "unavailable"))
    for agent, path in agent_status(config.claude_command):
        detail = path or agent.source
        checks.append(Check(f"agent:{agent.name}", "AVAILABLE" if path else "OPTIONAL", detail))
    checks.append(Check("CTFd submission", "OPTIONAL", "enabled" if config.allow_submission and config.ctfd_url and config.ctfd_token else "disabled by default"))
    return checks
