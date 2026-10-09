"""Offline ranking check (not a substitute for unseen reviewer test questions).

Run after ingestion: python eval_retrieval.py
Measures whether the correct evidence appears at rank 1 and in top 3.
"""
from retrieval import load_corpus, retrieve

# Labels indicate relevant DOCUMENT/SECTION, not answers prewritten in code.
CASES = [
    ("Dimana letak lokasi sumur?", "country", "DGOS", None),
    ("Berapa Total NPT sumur?", "cumulative_npt_hours", "DDR", 32),
    ("Wireline run apa yang direncanakan?", "next_24h_operation", "DGOS", 72),
    ("What does NPT mean?", "glossary:NPT", "GLOSSARY", None),
    ("What does MPSR mean?", "glossary:MPSR", "GLOSSARY", None),
    ("Berapa total NPT report 84?", "npt_total_hours", "DGOS", 84),
    ("Where is the well in report 84?", "country", "DGOS", 84),
    ("How many pretest points were acquired on September 10?", "remarks", "DGOS", 84),
    ("What happened to the Rhino Reamer?", "page_", "DDR", 32),
]
REFUSALS = [
    "Who won the football World Cup in 2014?",
    "Bagaimana cara memasak nasi goreng?",
    "What is the weather forecast for tomorrow?",
]


def matches(hit, expected):
    section, report_type, report_number = expected
    return (hit["section"].startswith(section) and hit["document_type"] == report_type
            and (report_number is None or hit["report_number"] == report_number))
