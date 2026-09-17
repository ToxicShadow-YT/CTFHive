from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from ctfhive.agents.coordinator import Coordinator
from ctfhive.config import Config
from ctfhive.doctor import run_checks
from ctfhive.evidence.store import EvidenceStore
from ctfhive.intake import ingest
from ctfhive.knowledge.research import format_items
from ctfhive.knowledge.store import KnowledgeStore
from ctfhive.models.ollama import OllamaModel
from ctfhive.tools.registry import ToolRegistry
from ctfhive.tools.agents import agent_status


RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
DIM = "\033[2m"


def color(text: str, code: str) -> str:
    return f"{code}{text}{RESET}" if sys.stdout.isatty() else text


def clear() -> None:
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")


def header(title: str) -> None:
    clear()
    print(color("CTFHIVE", BOLD + YELLOW))
    print(color("Autonomous CTF terminal operations console", DIM))
    print(color("=" * 58, CYAN))
    print(color(title, BOLD))
    print()


def config() -> Config:
    value = Config.from_env()
    value.ensure_dirs()
    return value


def show_doctor(value: Config) -> None:
    header("SYSTEM DIAGNOSTICS")
    for check in run_checks(value):
        mark = GREEN if check.status in {"AVAILABLE", "REQUIRED"} else YELLOW if check.status == "OPTIONAL" else RED
        print(f"{color(check.status, mark):12} {check.name:26} {check.detail}")
    input("\nPress Enter to return...")


def show_tools() -> None:
    header("TOOL REGISTRY")
    current = ""
    for tool, path in ToolRegistry().status():
        if tool.category != current:
            current = tool.category
            print(f"\n{color(current.upper(), CYAN)}")
        status = color("AVAILABLE", GREEN) if path else color("UNAVAILABLE", YELLOW)
        print(f"  {tool.name:18} {status:12} {path or ''}")
    input("\nPress Enter to return...")


def show_agents() -> None:
    header("EXTERNAL AGENT INTEGRATIONS")
    print(color("All external agents are disabled by default and require operator review.\n", YELLOW))
    for agent, path in agent_status(Config.from_env().claude_command):
        status = color("AVAILABLE", GREEN) if path else color("NOT INSTALLED", YELLOW)
        print(f"{agent.name:24} {status:14} {agent.source}")
        if agent.notes:
            print(f"  {agent.notes}")
    input("\nPress Enter to return...")


def show_knowledge(value: Config) -> None:
    header("KNOWLEDGE SEARCH")
    query = input("Search (blank lists recent): ").strip()
    items = KnowledgeStore(value.knowledge_path).search(query, limit=12, include_unapproved=True)
    print()
    if not items:
        print(color("No local knowledge records.", YELLOW))
    else:
        print(format_items(items))
    input("\nPress Enter to return...")


def show_evidence(value: Config) -> None:
    header("EVIDENCE")
    challenge = input("Challenge name (blank for all): ").strip()
    store = EvidenceStore(value.evidence_root)
    records = store.read(challenge) if challenge else list(store.all())
    if not records:
        print(color("No evidence records.", YELLOW))
    for record in records:
        print(f"\n{color(record.tool, CYAN)} | agent={record.agent} | exit={record.exit_code} | confidence={record.confidence:.2f}")
        if record.stdout:
            print(record.stdout[:2000])
        if record.stderr:
            print(color(record.stderr[:1000], RED))
        if record.observations:
            print(color("observations: " + "; ".join(record.observations), DIM))
    input("\nPress Enter to return...")


def solve(value: Config, path: str | None = None, mock: bool = True) -> None:
    header("SOLVE CHALLENGE")
    source = path or input("Challenge file or directory: ").strip()
    if not source:
        return
    mode = mock if path is not None else input("Mock mode? [Y/n]: ").strip().lower() not in {"n", "no"}
    try:
        challenge = ingest(source, value.workspace_root)
        print(f"{color('[+]', GREEN)} Challenge isolated: {challenge.name}")
        print(f"{color('[+]', GREEN)} Files inspected: {len(challenge.files)}")
        model = None if mode else OllamaModel(value.ollama_base_url, value.model)
        result = Coordinator(value, EvidenceStore(value.evidence_root), model=model).solve(challenge, mock=mode)
        print(f"{color('[+]', GREEN)} Category: {result.category.value}")
        print(f"{color('[+]', GREEN)} Status: {'SOLVED' if result.solved else 'NOT SOLVED'}")
        print(f"{color('[+]', GREEN)} Flag: {result.flag or 'none backed by evidence'}")
        for observation in result.observations:
            print(f"{color('[i]', CYAN)} {observation}")
    except (OSError, ValueError, ConnectionError) as error:
        print(color(f"[!] Solver failed safely: {error}", RED))
    if path is None:
        input("\nPress Enter to return...")


def menu(value: Config) -> None:
    while True:
        header("MAIN MENU")
        print("  1. Solve challenge")
        print("  2. System diagnostics")
        print("  3. Tool registry")
        print("  4. Evidence viewer")
        print("  5. Knowledge search")
        print("  6. External agent integrations")
        print("  7. Configuration")
        print("  q. Quit")
        choice = input("\nctfhive> ").strip().lower()
        if choice == "1":
            solve(value)
        elif choice == "2":
            show_doctor(value)
        elif choice == "3":
            show_tools()
        elif choice == "4":
            show_evidence(value)
        elif choice == "5":
            show_knowledge(value)
        elif choice == "6":
            show_agents()
        elif choice == "7":
            header("CONFIGURATION")
            print(f"Model:      {value.model}")
            print(f"Ollama:     {value.ollama_base_url}")
            print(f"Workspace:  {value.workspace_root}")
            print(f"Evidence:   {value.evidence_root}")
            print(f"Knowledge:  {value.knowledge_path}")
            print(f"Learning:   {value.learning_mode}")
            input("\nPress Enter to return...")
        elif choice in {"q", "quit", "exit"}:
            print("Goodbye.")
            return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ctfhive tui", description="Local CTFHive terminal UI")
    parser.add_argument("--solve", metavar="PATH", help="solve one challenge and exit")
    parser.add_argument("--real", action="store_true", help="use local tools and Ollama instead of mock mode")
    args = parser.parse_args(argv)
    value = config()
    if args.solve:
        solve(value, args.solve, mock=not args.real)
    else:
        menu(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
