from __future__ import annotations

from pathlib import Path

from ctfhive.cli import main
from ctfhive.knowledge.ingestion import import_text
from ctfhive.knowledge.models import KnowledgeItem, SourceType
from ctfhive.knowledge.security import safe_knowledge_text
from ctfhive.knowledge.store import KnowledgeStore


def test_knowledge_redacts_secrets_and_flags(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    item_id = store.add(KnowledgeItem("lesson", "rev", "validation", "FLAG{secret}", "token=abc FLAG{secret}", "test", SourceType.LOCAL_NOTE))
    item = store.get(item_id)
    assert item is not None
    assert "FLAG{" not in item.content
    assert "token=abc" not in item.content


def test_knowledge_retrieval_feedback_and_export(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    item_id = store.add(KnowledgeItem("PIE ROP", "pwn", "exploitation", "derive a base", "check protections before ROP", "local", SourceType.SOLVED_CHALLENGE, tags=["pie", "rop"]))
    assert store.search("PIE", category="pwn")[0].id == item_id
    store.update_feedback(item_id, True)
    assert store.get(item_id).success_count == 1
    export = tmp_path / "export.jsonl"
    assert store.export_jsonl(export) == 1
    imported = KnowledgeStore(tmp_path / "other.sqlite3")
    assert imported.import_jsonl(export) == 1


def test_text_import_classifies(tmp_path: Path):
    note = tmp_path / "rsa.md"
    note.write_text("RSA nonce reuse can reveal the private key", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    import_text(store, note)
    assert store.search("RSA")[0].category == "crypto"


def test_knowledge_cli_stats(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("CTFHIVE_KNOWLEDGE", str(tmp_path / "knowledge.sqlite3"))
    assert main(["knowledge", "stats"]) == 0
    assert '"records": 0' in capsys.readouterr().out
