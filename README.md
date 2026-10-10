# Qonnectiq Take Home Test

### Project Overview
Lightweight AI chatbot that allows users to ask questions about Oil & Gas drilling reports in natural language, without having to manually read through technical documents. The chatbot will support both English and Indonesian, provide answers based on the uploaded documents, and include source references.

#### **Important Note:** The development approach, technology choices, expected outcomes, work tracking, and MVP priorities are documented in [development_plan.md](development_plan.md).

### Prerequisites

- Python 3.11 or newer.
- An OpenAI API key for AI-generated answers and optional semantic embeddings.
- PDF well reports with a format similar to the provided DGOS and DDR documents.
- A DOCX glossary containing Oil & Gas terms and definitions.

### Installation

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

### Configuration

Copy the environment template:

```bash
cp .env.example .env
```

On Windows:

```powershell
copy .env.example .env
```

Add the reviewer-provided API key to `.env`:

```dotenv
OPENAI_API_KEY=openai-api-key
OPENAI_MODEL=gpt-4o-mini
PARSED_DATA_DIR=parsed_data
```

The `.env` file remains local and not committed.

### Add Input Documents

Place PDF reports and the glossary inside `datasets/`. Source documents and generated JSON files are not committed.

```text
datasets/
  Glossaries.docx
  example_dgos.pdf
  example_ddr.pdf
```

### Parse the Documents

Parse every supported document with one command:

```bash
python ingest.py
```

The command writes one structured JSON file per input document to `parsed_data/`. New similarly formatted PDFs are detected from their contents rather than their filenames.

To build the optional semantic embedding cache:

```bash
python ingest.py --embed
```

### Run the Chat Application

Start the API and browser interface:

```bash
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/`. The JSON API accepts `POST /api/chat` with `{"question": "What does BHA mean?"}`. Use `GET /api/health` to check whether parsed documents are available.

### Run Tests and Evaluation

```bash
python -m pytest -q
python eval_retrieval.py
```

The evaluation reports Top-1 accuracy, Recall@3, and out-of-scope rejection results for its labeled questions. It is a smoke-test suite rather than a performance claim for unknown reports.

## Architecture and Operation

```text
PDF / DOCX
  -> ingest.py -> parsers/ -> parsed_data/*.json
  -> retrieval.py: structured facts + BM25 + optional embeddings
  -> qa.py: direct fact answers or grounded OpenAI completion
  -> app.py: FastAPI API + minimal HTML/JavaScript chat
```

- **Parsing:** PyMuPDF processes DGOS and DDR PDFs, while python-docx reads glossary tables. Original page text and source metadata are preserved for retrieval and citations.
- **Storage:** JSON is used for the MVP because the corpus is small and the assignment requires no external service. SQLite remains a backlog enhancement.
- **Retrieval:** Structured field matching, bilingual keyword expansion, BM25, date and report-number filtering, and optional embedding reranking identify relevant evidence.
- **Answering:** Direct factual matches are returned without an LLM call. Other supported questions use GPT-4o-mini with only retrieved evidence in the prompt.
- **Interface:** FastAPI serves both the JSON API and the small browser client, avoiding a separate frontend toolchain.

## JSON Structure

Each parsed report produces one JSON file. Missing values use `null` rather than an assumed value.

```json
{
  "schema_version": 1,
  "document_type": "DGOS",
  "source_file": "example_dgos.pdf",
  "page_count": 1,
  "report_date": "2026-10-01",
  "report_number": 1,
  "well_name": "EXAMPLE-1",
  "country": "EXAMPLELAND",
  "current_depth_mddf": 1234.5,
  "next_24h_operation": "Inspect equipment.",
  "npt_details": [],
  "sections": [
    {"section": "next_24h_operation", "page": 1, "text": "Inspect equipment."}
  ],
  "pages": [
    {"page": 1, "text": "Original page text..."}
  ]
}
```

DDR records use the same source metadata and include fields such as `cumulative_npt_hours`, `daily_npt_hours`, `measured_depth_m`, and `cumulative_cost_usd`. Glossary records contain `terms` with a term, meaning, and confirmation flag. Optional embeddings are stored separately in `parsed_data/embeddings.json`.

## Resolution, Limitations, and Future Work

| Challenge | Current treatment | Future improvement |
|---|---|---|
| Overlapping DGOS labels | Use positioned extraction for important fields and operation boxes. | Add more layout fixtures from unseen reports. |
| Dense multi-page DDR tables | Extract typed header facts and preserve overlapping page chunks. | Expand field-level validation for additional templates. |
| Reports for the same well on different dates | Keep report dates and numbers on every evidence record. | Add broader held-out date-scoped evaluation. |
| Missing or unrelated information | Use evidence thresholds and a consistent refusal response. | Measure refusal precision and recall on a larger test set. |
| Scanned or image-only PDFs | Not supported in this MVP. | Add OCR and validate it against scanned samples. |
| Broader semantic retrieval | Provide optional OpenAI embedding reranking. | Consider a reranker only if evaluation results justify it. |
| Database persistence | Keep parsed output in local JSON files. | Add SQLite without requiring extra infrastructure. |

## Security and Submission Notes

- Never commit `.env`, API keys, source datasets, parsed JSON, or generated embeddings.
- Reviewers should use their own OpenAI API key.
- Confirm that source reports may be sent to OpenAI before enabling chat generation or semantic embeddings.
- This application is an assessment MVP and is not intended for production drilling decisions.
