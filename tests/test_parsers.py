"""Offline tests: synthetic fixtures plus optional integration against local datasets."""
from pathlib import Path

import fitz
import pytest
from docx import Document

from ingest import classify_pdf, run
from parsers import parse_ddr, parse_dgos, parse_glossary


