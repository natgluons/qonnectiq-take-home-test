"""Parser for the multi-page Daily Drilling / Daily Operation Report template."""
from __future__ import annotations

import re
from pathlib import Path
import fitz
from .common import clean, date_iso, normalized_pages, number, search, segment, source_record, chunk


def extract_status(text: str, field: str, next_field: str) -> str | None:
    # Layout includes wrap-around descriptions; match from one label to the next.
    regex = rf"(?im)^\s*{re.escape(field)}\s*:\s*(.*?)(?=^\s*{re.escape(next_field)}\s*:|\Z)"
    match = re.search(regex, text, re.S | re.M | re.I)
    return clean(match.group(1)) if match else None
