"""Parser for the one-page Daily Geological Operations Summary template.

Uses layout-relative windows to avoid duplicated overlay labels present in
these PDF forms. It also retains original page text for less common questions.
"""
from __future__ import annotations

import re
from pathlib import Path
import fitz
from .common import (
    clean, clipped_lines, date_iso, number, normalized_pages, search,
    segment, source_record, unique_lines,
)


def parse_operation(page: fitz.Page, y0: float, y1: float, label: str) -> str:
    # Source forms contain repeated "Last Ops Update" and "Next Update" overlays.
    ignored = {
        "current ops update", "last ops update", "next update",
        "npt", "current operation @ 0600 hrs :", "last 24 hrs operation",
        "next 24 hrs operation",
    }
    lines = clipped_lines(page, 0, y0, page.rect.width, y1)
    lines = [s for s in lines if s.lower() not in ignored and label.lower() not in s.lower() and s not in {"@", ":"}]
    return unique_lines(lines, ignored)
