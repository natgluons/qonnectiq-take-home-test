import sqlite3

from retrieval import load_corpus
from storage import load_sqlite_corpus, replace_corpus


CORPUS = [
    {
        "document_type": "DGOS",
        "source_file": "example.pdf",
        "report_date": "2026-10-10",
        "report_number": 10,
        "well_name": "EXAMPLE-1",
        "country": "MALAYSIA",
        "sections": [],
    },
    {
        "document_type": "GLOSSARY",
        "source_file": "Glossaries.docx",
        "terms": [{"term": "NPT", "meaning": "Non-Productive Time"}],
    },
]


def test_replace_and_load_sqlite_corpus(tmp_path):
    database = tmp_path / "corpus.db"
    assert replace_corpus(database, CORPUS) == 2
    expected = sorted(CORPUS, key=lambda document: document["source_file"])
    assert load_sqlite_corpus(database) == expected
    assert load_corpus(database) == expected


def test_replace_corpus_removes_stale_documents(tmp_path):
    database = tmp_path / "corpus.db"
    replace_corpus(database, CORPUS)
    replace_corpus(database, CORPUS[:1])
    assert load_sqlite_corpus(database) == CORPUS[:1]


def test_sqlite_schema_exposes_searchable_metadata(tmp_path):
    database = tmp_path / "corpus.db"
    replace_corpus(database, CORPUS)
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT document_type, report_date, report_number, well_name "
            "FROM documents WHERE source_file = ?",
            ("example.pdf",),
        ).fetchone()
    assert row == ("DGOS", "2026-10-10", 10, "EXAMPLE-1")
