"""Optional OpenAI semantic search, persisted as local JSON (no vector DB)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from retrieval import build_records, load_corpus

load_dotenv()
MODEL = "text-embedding-3-small"


def build_embedding_cache(output_dir: Path) -> int:
    """Run after ingestion with --embed. Reuse unchanged document chunks."""
    from openai import OpenAI

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY must be set to generate semantic embeddings")
    path = output_dir / "embeddings.json"
    try:
        stored = json.loads(path.read_text(encoding="utf8"))
    except (OSError, ValueError):
        stored = {}
    existing = stored.get("vectors", {}) if stored.get("model") == MODEL else {}
    records = build_records(load_corpus(output_dir))
    vectors = {e["id"]: existing[e["id"]] for e in records if e["id"] in existing}
    missing = [e for e in records if e["id"] not in vectors]
    if missing:
        client = OpenAI(timeout=60, max_retries=1)
        for i in range(0, len(missing), 64):
            batch = missing[i:i+64]
            response = client.embeddings.create(model=MODEL, input=[e["text"][:5000] for e in batch])
            for item in response.data:
                vectors[batch[item.index]["id"]] = item.embedding
    # Strip stale entries so removing a PDF removes its vectors too.
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps({"model": MODEL, "vectors": vectors}), encoding="utf8")
    temp.replace(path)
    return len(missing)


def load_embedding_cache(folder: Path) -> dict:
    try:
        data = json.loads((folder / "embeddings.json").read_text(encoding="utf8"))
        return data.get("vectors", {}) if data.get("model") == MODEL else {}
    except (OSError, ValueError):
        return {}


def embed_question(question: str) -> list[float]:
    from openai import OpenAI
    client = OpenAI(timeout=25, max_retries=1)
    return client.embeddings.create(model=MODEL, input=question).data[0].embedding
