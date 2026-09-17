from __future__ import annotations

import json
from pathlib import Path

from ctfhive.knowledge.models import KnowledgeItem, SourceType
from ctfhive.knowledge.store import KnowledgeStore
from ctfhive.knowledge.training import export_training_data


def test_training_export_is_generalized_and_redacted(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "knowledge.sqlite3")
    store.add(KnowledgeItem("rev strategy", "rev", "validation", "find comparisons", "FLAG{secret} token=bad; inspect validation", "local", SourceType.SOLVED_CHALLENGE))
    output = tmp_path / "qwen.jsonl"
    assert export_training_data(store, output) == 1
    record = json.loads(output.read_text(encoding="utf-8"))
    assert "FLAG{" not in record["response"]
    assert "token=bad" not in record["response"]
    assert "generalized" in record["instruction"]
