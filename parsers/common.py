"""Shared parsing helpers, source attribution, and PDF layout utilities."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz

NUM = r"[\d,]+(?:\.\d+)?"


def clean(value: str) -> str:
    """Normalize spaces without altering case or technical abbreviations."""
    return re.sub(r"\s+", " ", value or "").strip()


def number(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", ""))
    except (ValueError, TypeError):
        return None


def date_iso(text: str | None) -> str | None:
    if not text:
        return None
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def search(text: str, pattern: str, flags: int = re.I | re.S) -> str | None:
    found = re.search(pattern, text, flags)
    return clean(found.group(1)) if found else None


def normalized_pages(pdf: fitz.Document) -> list[dict[str, Any]]:
    return [
        {"page": i + 1, "text": pdf[i].get_text("text", sort=True)}
        for i in range(len(pdf))
    ]


def clipped_lines(page: fitz.Page, x0: float, y0: float, x1: float, y1: float) -> list[str]:
    """Extract an area without the destructive text mixing of PDF row sorting."""
    rect = fitz.Rect(x0, y0, x1, y1)
    lines = [clean(x) for x in page.get_text("text", clip=rect, sort=False).splitlines()]
    return [x for x in lines if x]


def unique_lines(lines: list[str], ignored: set[str] | None = None) -> str:
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        if line.lower() in (ignored or set()):
            continue
        if line in seen:
            continue
        seen.add(line)
        result.append(line)
    return clean(" ".join(result))


def fields_chunk(data: dict, fields: list[str] | None = None) -> str:
    fields = fields or list(data)
    return "; ".join(f"{k}: {data[k]}" for k in fields if data.get(k) is not None)


def chunk(page_text: str, max_chars: int = 1500, overlap: int = 180) -> list[str]:
    """Break long reports into answerable spans; preserve original page association."""
    paragraphs = [clean(p) for p in re.split(r"\n\s*\n", page_text) if clean(p)]
    out: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            out.append(paragraph)
            continue
        start = 0
        while start < len(paragraph):
            end = min(len(paragraph), start + max_chars)
            if end < len(paragraph):
                split_at = paragraph.rfind(" ", start + max_chars // 2, end)
                if split_at > start:
                    end = split_at
            out.append(paragraph[start:end].strip())
            if end == len(paragraph):
                break
            start = max(start + 1, end - overlap)
    return out
