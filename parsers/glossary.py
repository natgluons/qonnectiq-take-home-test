"""Extract terminology from real DOCX tables; no hardcoded glossary terms."""
from __future__ import annotations

from pathlib import Path
from docx import Document
from .common import clean


def parse_glossary(path: str | Path) -> dict:
    path = Path(path)
    doc = Document(path)
    terms: list[dict] = []
    seen: set[str] = set()
    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) < 2:
                continue
            term, meaning = (clean(row.cells[0].text), clean(row.cells[1].text))
            if not term or not meaning or term.lower() in {"part", "abbreviation"}:
                continue
            # Alphabet dividers such as "A | A" and "B | B" aren't definitions.
            if len(term) == 1 and term.upper() == term and meaning.upper() == term:
                continue
            key = term.casefold()
            if key in seen:
                continue
            seen.add(key)
            terms.append({
                "term": term,
                "meaning": meaning,
                "needs_confirmation": "to be confirmed" in meaning.lower() or meaning.lower().startswith("unknown"),
            })
    if not terms:
        raise ValueError(f"No glossary table rows found: {path.name}")
    return {
        "schema_version": 1,
        "document_type": "GLOSSARY",
        "source_file": path.name,
        "terms": terms,
    }
