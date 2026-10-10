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

from storage import load_sqlite_corpus

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
    source = Path(folder)
    if source.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        return load_sqlite_corpus(source)
    docs = []
    for path in sorted(source.glob("*.json")):
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


def _scope(question: str, corpus: list[dict]) -> tuple[str | None, int | None, str | None]:
    # Do not confuse WL Run #1 with report number 1.
    number = re.search(r"\b(?:report|laporan)(?:\s+(?:no\.?|number))?\s*#?\s*(\d{1,4})\b", question, re.I)
    date = _mentioned_date(question)
    wells = sorted({x["well_name"] for x in corpus if x.get("well_name")}, key=len, reverse=True)
    name = next((well for well in wells if well.lower() in question.lower()), None)
    return date, int(number.group(1)) if number else None, name


def _bm25(query: list[str], evidence: list[dict]) -> list[float]:
    tf = [Counter(tokenize(e["text"])) for e in evidence]
    lengths = [sum(x.values()) for x in tf]
    average_length = sum(lengths) / max(len(tf), 1)
    df = Counter(t for counter in tf for t in counter)
    n = len(tf)
    scores = []
    for counts, length in zip(tf, lengths):
        score = 0.0
        for word in set(query):
            count = counts.get(word, 0)
            if count:
                idf = math.log(1 + (n - df[word] + .5) / (df[word] + .5))
                score += idf * (count * 2.2) / (count + 1.2 * (.25 + .75 * length / max(average_length, 1)))
        scores.append(score)
    return scores


def retrieve(question: str, corpus: list[dict], limit: int = 6,
             vectors: dict[str, list[float]] | None = None,
             query_vector: list[float] | None = None) -> list[dict]:
    """Find attributed evidence. Optional embeddings blend with lexical BM25.

    Retrieval remains useful entirely offline; embeddings require no vector DB.
    """
    q = question.strip()
    # No report contains evidence about future conditions relative to the user.
    # This is not a general weather forecasting service.
    if re.search(r"\b(tomorrow|besok|next week|minggu depan|hari ini|today|sekarang|right now)\b", q, re.I) and \
            not re.search(r"\b(next 24|24 jam berikutnya)\b", q, re.I):
        return []
    tokens = query_tokens(q)
    if not tokens:
        return []
    date, report_number, well_name = _scope(q, corpus)
    evidence = [e for e in build_records(corpus)
                if (date is None or e["report_date"] is None or e["report_date"] == date)
                and (report_number is None or e["report_number"] is None or e["report_number"] == report_number)
                and (well_name is None or e["document_type"] == "GLOSSARY"
                     or any(d.get("source_file") == e["source_file"] and d.get("well_name") == well_name for d in corpus))]
    glossary_intent = bool(GLOSSARY_INTENT.search(q)) and not (
        (date is not None or report_number is not None) and
        re.search(r"\b(npt|cost|depth|mud|report|laporan|biaya|kedalaman)\b", q, re.I)
    )
    for e in evidence:
        if not e["section"].startswith("glossary:"):
            continue
        term = e["section"].split(":", 1)[1]
        # A general question containing "in" or "at" is not a glossary query.
        term_matched = re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", q, re.I)
        e["glossary_exact"] = bool(term_matched and glossary_intent)
    scores = _bm25(tokens, evidence)
    wants_npt = bool(re.search(r"\bnpt\b|non.productive|downtime", q, re.I))
    wants_total = bool(re.search(r"\b(total|cumulative|cumm|kumulatif)\b", q, re.I))
    wants_country = bool(re.search(r"\b(lokasi|location|country|negara|where|terletak|berada)\b", q, re.I))
    planned_wl = bool(re.search(r"\b(wireline|wl)\b", q, re.I)) and bool(re.search(
        r"\b(plan|planned|rencana|direncanakan|next|akan|forecast)\b", q, re.I))
    # Try exact type-and-field routing first; the model should never guess which
    # dated field a question about total NPT refers to.
    for e, score in zip(evidence, scores):
        field = e["section"]
        boost = 0.0
        if e.get("glossary_exact"):
            boost = 70.0
        elif field.startswith("glossary:"):
            # Keep definitions out of operational searches, including tiny units.
            score = 0 if not glossary_intent else score * .25
        elif field == "country" and wants_country:
            boost = 55.0
        elif field == "cumulative_npt_hours" and wants_npt and wants_total:
            boost = 70.0
        elif field in ("daily_npt_hours", "npt_total_hours", "npt_details") and wants_npt and not wants_total:
            boost = 35.0
        elif field == "npt_total_hours" and wants_npt and wants_total and (date or report_number):
            boost = 45.0
        elif field == "current_depth_mddf" and re.search(r"\b(current|kedalaman|depth|dalam)\b", q, re.I):
            boost = 20.0
        elif field == "cumulative_cost_usd" and re.search(r"\b(total|cumulative|biaya|cost)\b", q, re.I):
            boost = 15.0
        elif field.startswith("next_24h_operation") and planned_wl and re.search(r"\bWL\s+Run|wireline", e["text"], re.I):
            boost = 65.0
        if field.startswith("full_report") or field.startswith("raw_report"):
            score *= .40
        e["score"] = score + boost
    # True semantic re-ranking is optional. Require some lexical/domain evidence
    # to avoid answering off-topic requests solely on cosine similarity.
    if vectors and query_vector:
        query_norm = math.sqrt(sum(x*x for x in query_vector)) or 1.0
        for e in evidence:
            v = vectors.get(e["id"])
            if v and len(v) == len(query_vector):
                denom = query_norm * (math.sqrt(sum(x*x for x in v)) or 1.0)
                similarity = sum(a*b for a,b in zip(v,query_vector)) / denom
                if similarity > .30 and e["score"] > 0:
                    e["score"] += max(0, (similarity - .30)) * 13
    evidence = [e for e in evidence if e["score"] > 1.5 and
                (not e["section"].startswith("glossary:") or e.get("glossary_exact"))]
    evidence.sort(key=lambda e: e["score"], reverse=True)
    seen, ranked = set(), []
    for e in evidence:
        identity = (e["source_file"], e["page"], e["section"])
        if identity in seen:
            continue
        seen.add(identity)
        ranked.append(e)
        if len(ranked) == limit:
            break
    return ranked
