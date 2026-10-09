from qa import REFUSAL, answer
from retrieval import retrieve

CORPUS = [
    {
        "document_type": "DDR", "source_file": "demo_ddr.pdf", "report_date": "2026-07-19",
        "report_number": 32, "well_name": "DEMO-1", "rig_name": "RIG-1",
        "cumulative_npt_hours": 1.5, "daily_npt_hours": 1.5,
        "sections": [{"section": "last_24h_operation", "page": 1,
                      "text": "The drilling crew repaired an underreamer."}],
    },
    {
        "document_type": "DGOS", "source_file": "demo_dgos.pdf", "report_date": "2026-08-29",
        "report_number": 72, "well_name": "DEMO-1", "rig_name": "RIG-1", "country": "MALAYSIA",
        "next_24h_operation": "Perform WL Run #1: PEX-QAIT. Perform WL Run #2: MDT.",
        "sections": [{"section": "next_24h_operation", "page": 1,
                      "text": "Perform WL Run #1: PEX-QAIT. Perform WL Run #2: MDT."}],
    },
    {"document_type": "GLOSSARY", "source_file": "Glossaries.docx",
     "terms": [{"term": "BHA", "meaning": "Bottom Hole Assembly"}]},
]


def test_location():
    hits = retrieve("Dimana letak lokasi sumur?", CORPUS)
    assert hits[0]["section"] == "country"
    assert "MALAYSIA" in hits[0]["text"]


def test_total_npt():
    hits = retrieve("Berapa Total NPT sumur?", CORPUS)
    assert hits[0]["section"] == "cumulative_npt_hours"
    assert "1.5" in hits[0]["text"]


def test_planned_wireline():
    hits = retrieve("Wireline run apa yang direncanakan?", CORPUS)
    assert hits[0]["section"] == "next_24h_operation"
    assert "PEX-QAIT" in hits[0]["text"]


def test_glossary():
    hits = retrieve("What does BHA mean?", CORPUS)
    assert hits[0]["section"] == "glossary:BHA"


def test_out_of_scope_without_calling_openai():
    answer_text, sources = answer("Bagaimana cara memasak nasi goreng?", CORPUS, api_key="test-not-used")
    assert answer_text == REFUSAL
    assert sources == []


def test_known_answers_do_not_require_openai_key():
    assert answer("Dimana letak lokasi sumur?", CORPUS)[0] == "MALAYSIA"
    assert answer("Berapa Total NPT sumur?", CORPUS)[0] == "1.5 hr"
    assert "WL Run #1: PEX-QAIT" in answer("Wireline run apa yang direncanakan?", CORPUS)[0]
    assert "Bottom Hole Assembly" in answer("What does BHA mean?", CORPUS)[0]


def test_no_accidental_short_glossary_match():
    assert not retrieve("Who won the world cup in 2014?", CORPUS)
    assert not retrieve("What is the weather forecast for tomorrow?", CORPUS)


def test_report_number_restricts_retrieval():
    expanded = [*CORPUS, {
        "document_type": "DGOS", "source_file": "newer.pdf", "report_date": "2026-09-10",
        "report_number": 84, "well_name": "DEMO-1", "country": "MALAYSIA",
        "npt_total_hours": 2.25, "sections": [
            {"section": "remarks", "page": 1, "text": "Acquired 9 pretest points."}
        ],
    }]
    hits = retrieve("Berapa total NPT report 84?", expanded)
    assert hits[0]["section"] == "npt_total_hours"
    assert hits[0]["report_number"] == 84
    assert answer("Berapa total NPT report 84?", expanded)[0].startswith("2.25 hr")
    assert retrieve("Where is the well in report 999?", expanded) == []
