"""Shared parsing helpers, source attribution, and PDF layout utilities."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz

NUM = r"[\d,]+(?:\.\d+)?"


def clean(value: str) -> str:
    """Normalize spaces without altering case or technical abbreviations."""
    return re.sub(r"\s+", " ", value or "").strip()


def number(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", ""))
    except (ValueError, TypeError):
        return None


def date_iso(text: str | None) -> str | None:
    if not text:
        return None
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None
