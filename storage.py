"""SQLite persistence for parsed document records."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    source_file TEXT PRIMARY KEY,
    document_type TEXT NOT NULL,
    report_date TEXT,
    report_number INTEGER,
    well_name TEXT,
    content_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_report ON documents(report_date, report_number);
CREATE INDEX IF NOT EXISTS idx_documents_well ON documents(well_name);
"""


def replace_corpus(database: str | Path, documents: list[dict]) -> int:
    """Atomically replace the SQLite corpus with parsed documents."""
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute("DELETE FROM documents")
        connection.executemany(
            """INSERT INTO documents
               (source_file, document_type, report_date, report_number, well_name, content_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (
                    doc["source_file"],
                    doc["document_type"],
                    doc.get("report_date"),
                    doc.get("report_number"),
                    doc.get("well_name"),
                    json.dumps(doc, ensure_ascii=False),
                )
                for doc in documents
            ],
        )
    return len(documents)


def load_sqlite_corpus(database: str | Path) -> list[dict]:
    """Load parsed documents from SQLite, returning an empty corpus if absent."""
    path = Path(database)
    if not path.is_file():
        return []
    try:
        with sqlite3.connect(path) as connection:
            rows = connection.execute(
                "SELECT content_json FROM documents ORDER BY source_file"
            ).fetchall()
    except sqlite3.Error:
        return []
    documents = []
    for (content,) in rows:
        try:
            parsed = json.loads(content)
        except (TypeError, ValueError):
            continue
        if parsed.get("document_type") in {"DDR", "DGOS", "GLOSSARY"}:
            documents.append(parsed)
    return documents
