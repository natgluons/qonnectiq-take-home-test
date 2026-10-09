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


