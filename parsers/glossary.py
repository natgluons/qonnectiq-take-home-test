"""Extract terminology from real DOCX tables; no hardcoded glossary terms."""
from __future__ import annotations

from pathlib import Path
from docx import Document
from .common import clean


