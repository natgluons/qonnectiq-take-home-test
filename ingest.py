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


def run(input_dir: Path, output_dir: Path) -> dict:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input folder doesn't exist: {input_dir}")
    candidates = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".docx"}
        and not p.name.startswith("~$")
    )
    if not candidates:
        raise ValueError(f"No .pdf or .docx input files found in {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    failures: list[dict] = []
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
            target = output_dir / output_name(path, input_dir)
            # Atomic replace prevents truncated JSON when an ingestion is retried.
            tmp = target.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(target)
            LOG.info("%-8s %-62s -> %s", parsed["document_type"], path.name, target.name)
            created.append(str(target))
        except (ValueError, RuntimeError, OSError, KeyError) as exc:
            LOG.error("Unable to ingest %s: %s", path.name, exc)
            failures.append({"filename": path.name, "error": str(exc)})
    return {"files_created": created, "errors": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("datasets"))
    parser.add_argument("--output", type=Path, default=Path("parsed_data"))
    parser.add_argument("--embed", action="store_true", help="Also build cached OpenAI embeddings for hybrid retrieval")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        result = run(args.input, args.output)
    except (ValueError, FileNotFoundError) as exc:
        LOG.error("%s", exc)
        return 1
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
