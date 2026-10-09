"""Parser for the multi-page Daily Drilling / Daily Operation Report template."""
from __future__ import annotations

import re
from pathlib import Path
import fitz
from .common import clean, date_iso, normalized_pages, number, search, segment, source_record, chunk


