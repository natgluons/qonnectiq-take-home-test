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


def main():
    corpus = load_corpus()
    if not corpus:
        raise SystemExit("Run python ingest.py first")
    top1 = top3 = 0
    for question, section, report_type, report_number in CASES:
        hits = retrieve(question, corpus)
        expected = (section, report_type, report_number)
        rank = next((i + 1 for i, hit in enumerate(hits) if matches(hit, expected)), None)
        top1 += rank == 1
        top3 += rank is not None and rank <= 3
        print(f"{'PASS' if rank == 1 else 'CHECK':5} rank={rank or '-':>2}  {question}")
    refusals = sum(not retrieve(question, corpus) for question in REFUSALS)
    print(f"Top-1: {top1}/{len(CASES)}; Recall@3: {top3}/{len(CASES)}; "
          f"Out-of-scope rejected: {refusals}/{len(REFUSALS)}")
    return top1 == len(CASES) and refusals == len(REFUSALS)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
