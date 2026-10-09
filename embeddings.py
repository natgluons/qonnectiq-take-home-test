"""Optional OpenAI semantic search, persisted as local JSON (no vector DB)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from retrieval import build_records, load_corpus

load_dotenv()
MODEL = "text-embedding-3-small"


