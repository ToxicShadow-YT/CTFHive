from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ctfhive.agents.coordinator import Coordinator
from ctfhive.config import Config
from ctfhive.doctor import run_checks
from ctfhive.evidence.store import EvidenceStore
from ctfhive.intake import ingest
from ctfhive.models.ollama import OllamaModel
from ctfhive.tools.registry import ToolRegistry
from ctfhive.knowledge.ingestion import import_text
from ctfhive.knowledge.models import SourceType
from ctfhive.knowledge.research import format_items
from ctfhive.knowledge.store import KnowledgeStore
from ctfhive.knowledge.github import search_repositories
from ctfhive.knowledge.web import research_web
from ctfhive.knowledge.harvest import harvest_github
from ctfhive.knowledge.training import export_training_data, training_status
from ctfhive.tools.agents import agent_status


def _config() -> Config:
    config = Config.from_env()
    config.ensure_dirs()
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ctfhive", description="Safe autonomous CTF orchestration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor")
    doctor.set_defaults(action="doctor")
    tools = subparsers.add_parser("tools")
    tools.set_defaults(action="tools")
    evidence = subparsers.add_parser("evidence")
    evidence.add_argument("challenge", nargs="?")
    evidence.set_defaults(action="evidence")
    config_parser = subparsers.add_parser("config")
    config_parser.set_defaults(action="config")
    solve = subparsers.add_parser("solve-challenge")
    solve.add_argument("challenge")
    solve.add_argument("--category", choices=["web", "pwn", "rev", "crypto", "forensics", "stego", "osint", "misc"])
    solve.add_argument("--mock", action="store_true")
    solve.add_argument("--no-submit", action="store_true")
    solve.add_argument("--manual-submit", action="store_true")
    solve.set_defaults(action="solve")
    knowledge = subparsers.add_parser("knowledge")
    knowledge.add_argument("action_name", choices=["search", "stats", "import", "export", "learn", "harvest", "training-data", "train"])
    knowledge.add_argument("value", nargs="?")
    knowledge.add_argument("--limit", type=int, default=5)
    knowledge.set_defaults(action="knowledge")
    research = subparsers.add_parser("research")
    research.add_argument("kind", choices=["github", "web"])
    research.add_argument("query")
    research.set_defaults(action="research")
    tui = subparsers.add_parser("tui", help="start the local terminal UI")
    tui.add_argument("--solve", metavar="PATH")
    tui.add_argument("--real", action="store_true", help="use local tools and Ollama")
    tui.set_defaults(action="tui")
    agents = subparsers.add_parser("agents", help="list external agent integrations")
    agents.set_defaults(action="agents")
    args = parser.parse_args(argv)
    config = _config()

    if args.action == "tui":
        from ctfhive.tui import main as tui_main
        tui_args = []
        if args.solve:
            tui_args.extend(["--solve", args.solve])
        if args.real:
            tui_args.append("--real")
        return tui_main(tui_args)

    if args.action == "doctor":
        for check in run_checks(config):
            print(f"{check.status:12} {check.name:24} {check.detail}")
        return 0
    if args.action == "tools":
        for tool, path in ToolRegistry().status():
            print(f"{tool.category:12} {tool.name:16} {path or 'UNAVAILABLE'}")
        return 0
    if args.action == "agents":
        for agent, path in agent_status(config.claude_command):
            print(f"{agent.name:24} {path or 'NOT INSTALLED':16} {agent.source}")
        return 0
    if args.action == "config":
        print(json.dumps({"model": config.model, "ollama_base_url": config.ollama_base_url, "workspace_root": str(config.workspace_root), "evidence_root": str(config.evidence_root), "knowledge_path": str(config.knowledge_path), "learning_mode": config.learning_mode, "allow_submission": config.allow_submission, "ctfd_configured": bool(config.ctfd_url and config.ctfd_token)}, indent=2))
        return 0
    if args.action == "knowledge":
        store = KnowledgeStore(config.knowledge_path)
        if args.action_name == "stats":
            print(json.dumps({"records": store.count(), "path": str(config.knowledge_path)}))
        elif args.action_name == "search":
            print(format_items(store.search(args.value or "", limit=20, include_unapproved=True)))
        elif args.action_name == "import":
            path = Path(args.value or "")
            files = [file for file in path.rglob("*") if file.suffix.lower() in {".md", ".txt", ".json", ".jsonl"}] if path.is_dir() else [path]
            print(json.dumps({"imported": sum(import_text(store, file, SourceType.USER_WRITEUP) for file in files)}))
        elif args.action_name == "export":
            print(json.dumps({"exported": store.export_jsonl(Path(args.value or "knowledge/exported.jsonl"))}))
        elif args.action_name == "harvest":
            try:
                items = harvest_github(args.value or "CTF writeups", store, args.limit)
                print(json.dumps({"harvested": len(items), "message": "generalized public knowledge stored; challenge flags were redacted"}))
            except (OSError, ValueError, json.JSONDecodeError) as error:
                print(f"knowledge harvest unavailable: {error}", file=sys.stderr)
                return 2
        elif args.action_name == "training-data":
            target = Path(args.value or "knowledge/training/qwen.jsonl")
            print(json.dumps({"examples": export_training_data(store, target), "path": str(target), "format": "instruction-response-jsonl"}))
        elif args.action_name == "train":
            status = training_status()
            print(json.dumps({"weights_updated": False, **status, "next_step": "Review the generated dataset and run an approved Qwen fine-tuning command explicitly."}, indent=2))
        else:
            print("learn is performed automatically after solve-challenge")
        return 0
    if args.action == "research":
        store = KnowledgeStore(config.knowledge_path)
        try:
            results = search_repositories(args.query, store) if args.kind == "github" else research_web(args.query, store)
            print(json.dumps(results, indent=2))
        except OSError as error:
            print(f"research unavailable: {error}", file=sys.stderr)
            return 2
        return 0
    if args.action == "evidence":
        records = EvidenceStore(config.evidence_root)
        selected = list(records.all()) if not args.challenge else records.read(args.challenge)
        for record in selected:
            print(json.dumps(record.to_dict(), sort_keys=True))
        return 0
    challenge = ingest(args.challenge, config.workspace_root)
    model = None if args.mock else OllamaModel(config.ollama_base_url, config.model)
    result = Coordinator(config, EvidenceStore(config.evidence_root), model=model).solve(challenge, args.category, args.mock)
    print(json.dumps({"challenge": challenge.name, "category": result.category, "solved": result.solved, "flag": result.flag, "observations": result.observations}, indent=2))
    if result.flag and not args.no_submit and not args.manual_submit:
        print("Submission disabled: use --manual-submit or explicit CTFd configuration and CTFHIVE_ALLOW_SUBMISSION=true.")
    if result.flag and args.manual_submit:
        print(f"Manual submission candidate: {result.flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
