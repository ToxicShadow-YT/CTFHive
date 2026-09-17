from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import KnowledgeItem
from .security import safe_knowledge_text


_SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge (
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL,
 topic TEXT NOT NULL, summary TEXT NOT NULL, content TEXT NOT NULL, source TEXT NOT NULL,
 source_type TEXT NOT NULL, url TEXT, challenge TEXT, tags TEXT NOT NULL, confidence REAL NOT NULL,
 source_quality TEXT NOT NULL, evidence_count INTEGER NOT NULL, success_count INTEGER NOT NULL,
 failure_count INTEGER NOT NULL, approved INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON knowledge(topic);
"""


class KnowledgeStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def add(self, item: KnowledgeItem, *, redact: bool = True) -> int:
        if redact:
            item.summary = safe_knowledge_text(item.summary)
            item.content = safe_knowledge_text(item.content)
        values = item.to_record()
        values.pop("id")
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        with self._connect() as connection:
            cursor = connection.execute(f"INSERT INTO knowledge ({columns}) VALUES ({placeholders})", tuple(values.values()))
            item.id = int(cursor.lastrowid)
            return item.id

    def get(self, item_id: int) -> KnowledgeItem | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM knowledge WHERE id = ?", (item_id,)).fetchone()
        return KnowledgeItem.from_record(dict(row)) if row else None

    def search(self, query: str = "", category: str | None = None, limit: int = 8, include_unapproved: bool = False) -> list[KnowledgeItem]:
        terms = [term.lower() for term in query.split() if term]
        clauses = []
        params: list[object] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if not include_unapproved:
            clauses.append("approved = 1")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(f"SELECT * FROM knowledge {where} ORDER BY confidence DESC, success_count DESC, updated_at DESC LIMIT ?", (*params, max(limit * 5, limit))).fetchall()
        items = [KnowledgeItem.from_record(dict(row)) for row in rows]
        if not terms:
            return items[:limit]
        ranked = sorted(items, key=lambda item: sum(term in (item.title + " " + item.topic + " " + item.summary + " " + item.content + " " + " ".join(item.tags)).lower() for term in terms), reverse=True)
        return [item for item in ranked if any(term in (item.title + " " + item.topic + " " + item.summary + " " + item.content).lower() for term in terms)][:limit]

    def update_feedback(self, item_id: int, success: bool) -> None:
        field = "success_count" if success else "failure_count"
        with self._connect() as connection:
            connection.execute(f"UPDATE knowledge SET {field} = {field} + 1, evidence_count = evidence_count + 1, updated_at = datetime('now') WHERE id = ?", (item_id,))

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0])

    def export_jsonl(self, path: Path) -> int:
        items = self.search("", limit=1_000_000, include_unapproved=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(item.to_record(), sort_keys=True) for item in items) + ("\n" if items else ""), encoding="utf-8")
        return len(items)

    def import_jsonl(self, path: Path) -> int:
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                record.pop("id", None)
                self.add(KnowledgeItem.from_record(record))
                count += 1
        return count

    def all(self) -> Iterable[KnowledgeItem]:
        yield from self.search("", limit=1_000_000, include_unapproved=True)
