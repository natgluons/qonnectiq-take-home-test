"""Rebuild the searchable JSON corpus from a dataset directory.

Usage: python ingest.py [--input datasets] [--output parsed_data]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import fitz
from parsers import parse_ddr, parse_dgos, parse_glossary

LOG = logging.getLogger("ingest")


def classify_pdf(path: Path) -> str:
    """Identify a report by its document title, not by filename."""
    with fitz.open(path) as pdf:
        if not pdf.page_count:
            raise ValueError("Empty PDF")
        first = pdf[0].get_text("text").upper()
    if "DAILY GEOLOGICAL OPERATIONS SUMMARY" in first:
        return "DGOS"
    if "DAILY OPERATION REPORT" in first or "DAILY DRILLING REPORT" in first:
        return "DDR"
    raise ValueError("Unsupported PDF report layout (expected DGOS or DDR)")


def output_name(path: Path, root: Path) -> str:
    # Avoid collisions between same-named PDFs in different input subfolders.
    relative = str(path.relative_to(root).with_suffix(""))
    return re.sub(r"[^\w-]+", "_", relative).strip("_") + ".json"
