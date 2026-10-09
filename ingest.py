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


