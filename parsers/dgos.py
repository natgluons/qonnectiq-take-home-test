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


