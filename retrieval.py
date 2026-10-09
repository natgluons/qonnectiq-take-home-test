"""Document retrieval: typed facts + BM25 + optional semantic re-ranking.

No vector database or LLM framework: the parsed corpus is deliberately small.
Every hit is traceable to a source file, page, report and section.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path

STOP = set("""apa apakah adalah yang ini itu nya di dimana letak berapa bagaimana siapa
kapan dari dan atau untuk pada dalam tentang berdasarkan data sumur well wellnya
what which who when where is are was were the a an of in on at for to
how much many tell me please show explain report laporan dokumen document
informasi info berikan saya hasil and dengan by about its it did done do does
tersebut untuknya what 's""".split())

# Only light domain aliases, not a hard-coded answer dataset. This enables
# cross-language queries without requiring a paid embedding API call.
ALIASES = {
    "direncanakan": ("planned", "next", "forecast", "operation"),
    "rencana": ("planned", "next", "forecast", "operation"),
    "planned": ("next", "forecast"),
    "lokasi": ("country", "location", "region"),
    "negara": ("country", "location"),
    "letak": ("location", "country"),
    "berada": ("country", "location"),
    "biaya": ("cost", "usd"),
    "kedalaman": ("depth", "mddf", "md", "tvd"),
    "pengeboran": ("drilling", "drill", "operation"),
    "operasi": ("operation", "drilling"),
    "kerusakan": ("broken", "failed", "troubleshoot"),
    "masalah": ("failure", "failed", "troubleshoot"),
    "sampel": ("sampling", "sample"),
    "gas": ("gas", "flid"),
    "jumlah": ("total", "number"),
    "artinya": ("meaning", "definition"),
    "singkatan": ("abbreviation", "meaning"),
    "wireline": ("wl", "wireline"),
    "total": ("cumulative", "cumm"),
    "cumulative": ("total", "cumm"),
    "downtime": ("npt", "nonproductive"),
    "formation": ("lithology", "geological"),
    "testing": ("test", "pretest"),
    "weather": ("wind", "cloudy", "temperature"),
}

# Exclude only short generic unit terms from accidental matches (e.g. "in").
GLOSSARY_INTENT = re.compile(
    r"\b(?:what\s+(?:does|is|are)|what\s+stands\s+for|meaning|define|"
    r"abbreviation|stands\s+for|singkatan|apa\s+itu|artinya|arti\s+dari|"
    r"kepanjangan|berarti|maksud\s+dari|jelaskan\s+istilah)\b", re.I
)

FIELDS = {
    "well_name": "Well name",
    "country": "Country location",
    "block": "Block",
    "rig_name": "Rig name",
    "report_date": "Report date",
    "report_number": "Report number",
    "current_depth_mddf": "Current drilling depth mMDDF",
    "measured_depth_m": "Measured drilling depth MD",
    "true_vertical_depth_m": "True vertical depth TVD",
    "water_depth_m": "Water depth",
    "mud_weight_ppg": "Mud weight density ppg",
    "cumulative_npt_hours": "Cumulative total NPT non-productive time hours",
    "daily_npt_hours": "Daily NPT non-productive time hours",
    "npt_total_hours": "Daily NPT total reported hours",
    "daily_cost_usd": "Daily cost USD",
    "cumulative_cost_usd": "Cumulative total cost USD",
    "afe_cost_usd": "AFE cost approved budget USD",
}


def tokenize(value: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+(?:[-_/][a-z0-9]+)*", value.casefold())
            if t not in STOP and len(t) > 1]


def query_tokens(value: str) -> list[str]:
    tokens = tokenize(value)
    return tokens + [word for token in tokens for word in ALIASES.get(token, ())]


def load_corpus(folder: str | Path = "parsed_data") -> list[dict]:
    docs = []
    for path in sorted(Path(folder).glob("*.json")):
        try:
            parsed = json.loads(path.read_text(encoding="utf8"))
        except (OSError, ValueError):
            continue
        if parsed.get("document_type") in {"DDR", "DGOS", "GLOSSARY"}:
            docs.append(parsed)
    return docs


def _evidence(doc: dict, section: str, text: str, page: int = 1) -> dict:
    entry = {
        "source_file": doc["source_file"], "page": page, "section": section,
        "report_date": doc.get("report_date"), "report_number": doc.get("report_number"),
        "document_type": doc["document_type"], "text": text,
    }
    entry["id"] = sha256(f"{entry['source_file']}\0{page}\0{section}\0{text}".encode()).hexdigest()[:24]
    return entry


def build_records(corpus: list[dict]) -> list[dict]:
    records = []
    for doc in corpus:
        if doc.get("document_type") == "GLOSSARY":
            for term in doc.get("terms", []):
                records.append(_evidence(doc, "glossary:" + term["term"],
                                         f"{term['term']}: {term['meaning']}"))
            continue
        for key, display in FIELDS.items():
            value = doc.get(key)
            if value is not None and value != "":
                suffix = " hr" if key.endswith("hours") else (" ppg" if key == "mud_weight_ppg" else "")
                records.append(_evidence(doc, key, f"{display}: {value}{suffix}"))
        for section in doc.get("sections", []):
            text = section.get("text", "")
            if not text:
                continue
            # Keep indexed chunks bounded so a giant PDF page doesn't drown a
            # short and precise record. Source attribution remains page-based.
            if len(text) <= 1400:
                records.append(_evidence(doc, section["section"], text, section.get("page", 1)))
            else:
                for idx, part in enumerate(_slices(text)):
                    records.append(_evidence(doc, f"{section['section']}_part_{idx+1}",
                                             part, section.get("page", 1)))
        if doc.get("npt_raw"):
            records.append(_evidence(doc, "npt_details", "Daily NPT: " + doc["npt_raw"]))
    return records


def _slices(text: str, size: int = 1250, overlap: int = 150):
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            last = text.rfind(" ", start + size // 2, end)
            if last > start:
                end = last
        yield text[start:end]
        if end == len(text):
            return
        start = max(start + 1, end - overlap)


def _mentioned_date(question: str) -> str | None:
    iso = re.search(r"\b(\d{4})-(\d\d)-(\d\d)\b", question)
    if iso:
        return iso.group()
    day_first = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", question)
    if day_first:
        try:
            return datetime.strptime(day_first.group(), "%d/%m/%Y" if "/" in day_first.group() else "%d-%m-%Y").date().isoformat()
        except ValueError:
            return None
    months = "january february march april may june july august september october november december".split()
    for i, month in enumerate(months, 1):
        for name in (month, month[:3]):
            p1 = re.search(rf"\b{name}\s+(\d{{1,2}})(?:,?\s+(\d{{4}}))?\b", question, re.I)
            p2 = re.search(rf"\b(\d{{1,2}})\s+{name}(?:\s+(\d{{4}}))?\b", question, re.I)
            m = p1 or p2
            if m:
                try:
                    return datetime(int(m.group(2) or 2026), i, int(m.group(1))).date().isoformat()
                except ValueError:
                    return None
    return None
