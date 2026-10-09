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
