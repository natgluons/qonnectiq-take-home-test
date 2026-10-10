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
from storage import replace_corpus

LOG = logging.getLogger("ingest")


def classify_pdf(path: Path) -> str:
    """Identify a report by its document title, not by filename."""
    with fitz.open(path) as pdf:
        if not pdf.page_count:
            raise ValueError("Empty PDF")
        first = pdf[0].get_text("text").upper()
    if "DAILY GEOLOGICAL OPERATIONS SUMMARY" in first:
        return "DGOS"
    if "DAILY OPERATION REPORT" in first or "DAILY DRILLING REPORT" in first:
        return "DDR"
    raise ValueError("Unsupported PDF report layout (expected DGOS or DDR)")


def output_name(path: Path, root: Path) -> str:
    # Avoid collisions between same-named PDFs in different input subfolders.
    relative = str(path.relative_to(root).with_suffix(""))
    return re.sub(r"[^\w-]+", "_", relative).strip("_") + ".json"


def run(input_dir: Path, output_dir: Path, database_path: Path | None = None) -> dict:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input folder doesn't exist: {input_dir}")
    candidates = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".docx"}
        and not p.name.startswith("~$")
    )
    if not candidates:
        raise ValueError(f"No .pdf or .docx input files found in {input_dir}")
    if database_path is None:
        output_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    failures: list[dict] = []
    documents: list[dict] = []
    for path in candidates:
        try:
            if path.suffix.lower() == ".docx":
                if "gloss" not in path.stem.lower():
                    LOG.info("Ignoring non-glossary DOCX: %s", path.name)
                    continue
                parsed = parse_glossary(path)
            else:
                kind = classify_pdf(path)
                parsed = parse_dgos(path) if kind == "DGOS" else parse_ddr(path)
            documents.append(parsed)
            if database_path is None:
                target = output_dir / output_name(path, input_dir)
                # Atomic replace prevents truncated JSON when an ingestion is retried.
                tmp = target.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
                tmp.replace(target)
                LOG.info("%-8s %-62s -> %s", parsed["document_type"], path.name, target.name)
                created.append(str(target))
            else:
                LOG.info("%-8s %s", parsed["document_type"], path.name)
        except (ValueError, RuntimeError, OSError, KeyError) as exc:
            LOG.error("Unable to ingest %s: %s", path.name, exc)
            failures.append({"filename": path.name, "error": str(exc)})
    database = None
    if database_path is not None:
        replace_corpus(database_path, documents)
        database = str(database_path)
        LOG.info("SQLITE  %-62s <- %d document(s)", database_path, len(documents))
    return {"files_created": created, "database": database, "errors": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("datasets"))
    parser.add_argument("--output", type=Path, default=Path("parsed_data"))
    parser.add_argument("--database", type=Path,
                        help="Store in SQLite instead of JSON, for example parsed_data/corpus.db")
    parser.add_argument("--embed", action="store_true", help="Also build cached OpenAI embeddings for hybrid retrieval")
    args = parser.parse_args()
    if args.database and args.embed:
        parser.error("--embed currently requires the default JSON storage mode")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        result = run(args.input, args.output, args.database)
    except (ValueError, FileNotFoundError) as exc:
        LOG.error("%s", exc)
        return 1
    if result["database"]:
        print(f"Stored parsed corpus in SQLite: {result['database']}")
    else:
        print(f"Generated {len(result['files_created'])} JSON file(s)")
    if args.embed and result["files_created"] and not result["errors"]:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            from embeddings import build_embedding_cache
            count = build_embedding_cache(args.output)
            print(f"Semantic search: {count} new evidence embeddings cached")
        except Exception as exc:
            LOG.error("Embedding generation failed: %s", type(exc).__name__)
            return 1
    if result["errors"]:
        print(f"Errors: {len(result['errors'])}. See messages above.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
