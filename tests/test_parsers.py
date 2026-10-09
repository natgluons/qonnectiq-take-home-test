"""Offline tests: synthetic fixtures plus optional integration against local datasets."""
from pathlib import Path

import fitz
import pytest
from docx import Document

from ingest import classify_pdf, run
from parsers import parse_ddr, parse_dgos, parse_glossary


def test_glossary_docx_table(tmp_path):
    p = tmp_path / "Glossaries.docx"
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Abbreviation"
    table.rows[0].cells[1].text = "Meaning"
    for a, b in [("A", "A"), ("NPT", "Non-Productive Time – downtime"),
                 ("WIP", "Unknown – (to be confirmed)")]:
        row = table.add_row()
        row.cells[0].text, row.cells[1].text = a, b
    doc.save(p)
    result = parse_glossary(p)
    assert len(result["terms"]) == 2
    assert result["terms"][0]["term"] == "NPT"
    assert result["terms"][1]["needs_confirmation"] is True
