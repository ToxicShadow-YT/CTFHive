from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import StrEnum


class AgentSafety(StrEnum):
    REVIEW_REQUIRED = "review-required"
    DISABLED = "disabled-by-default"


@dataclass(frozen=True)
class ExternalAgent:
    name: str
    purpose: str
    source: str
    command: str | None = None
    safety: AgentSafety = AgentSafety.DISABLED
    notes: str = ""

    def availability(self) -> str | None:
        return shutil.which(self.command) if self.command else None


EXTERNAL_AGENTS: tuple[ExternalAgent, ...] = (
    ExternalAgent("PentestGPT", "AI-assisted penetration testing", "https://github.com/GreyDGL/PentestGPT", notes="Research project; review prompts and scope before use."),
    ExternalAgent("PentestAgent", "Autonomous pentesting workflows", "https://github.com/search?q=PentestAgent&type=repositories", notes="Repository/source must be verified and configured by the operator before enabling."),
    ExternalAgent("AutoPentest-DRL", "Automated penetration-testing research", "https://github.com/search?q=AutoPentest-DRL&type=repositories", notes="Research integration search; no automatic execution."),
    ExternalAgent("XBOW", "Autonomous security testing", "https://xbow.com/", notes="External commercial service; never upload challenge data implicitly."),
    ExternalAgent("Horizon3.ai NodeZero", "Automated penetration testing", "https://www.horizon3.ai/nodezero/", notes="External commercial service; explicit authorization required."),
    ExternalAgent("CAI", "Cybersecurity AI agents and tools", "https://github.com/aliasrobotics/cai", notes="External agent framework; review tool permissions."),
    ExternalAgent("Strix", "Autonomous security testing", "https://github.com/usestrix/strix", notes="External project; run only inside an isolated authorized target scope."),
    ExternalAgent("Shannon", "Autonomous web application security testing", "https://github.com/KeygraphHQ/shannon", notes="External project; network access must be explicitly enabled."),
    ExternalAgent("PentAGI", "Autonomous penetration testing", "https://github.com/vxcontrol/pentagi", notes="External project; never auto-run against an unapproved target."),
    ExternalAgent("HexStrike AI", "Security-tool orchestration", "https://github.com/0x4m4/hexstrike-ai", notes="External project; review generated actions before execution."),
    ExternalAgent("Claude Code", "Terminal and code agent", "https://github.com/anthropics/claude-code", command="claude", safety=AgentSafety.REVIEW_REQUIRED, notes="Optional escalation; no API key is read or displayed by CTFHive."),
    ExternalAgent("OpenHands", "Autonomous terminal and software agent", "https://github.com/All-Hands-AI/OpenHands", command="openhands", notes="Optional external agent; disabled by default."),
    ExternalAgent("Cline", "Agentic terminal workflow", "https://github.com/cline/cline", notes="VS Code extension integration; not a CTFHive subprocess."),
    ExternalAgent("Roo Code", "Agentic terminal workflow", "https://github.com/RooCodeInc/Roo-Code", notes="VS Code extension integration; not a CTFHive subprocess."),
)


def agent_status(claude_command: str = "claude") -> list[tuple[ExternalAgent, str | None]]:
    statuses: list[tuple[ExternalAgent, str | None]] = []
    for agent in EXTERNAL_AGENTS:
        if agent.name == "Claude Code" and claude_command != "claude":
            agent = ExternalAgent(agent.name, agent.purpose, agent.source, claude_command, agent.safety, agent.notes)
        statuses.append((agent, agent.availability()))
    return statuses
