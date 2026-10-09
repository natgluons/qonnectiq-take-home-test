"""Shared parsing helpers, source attribution, and PDF layout utilities."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz

NUM = r"[\d,]+(?:\.\d+)?"


