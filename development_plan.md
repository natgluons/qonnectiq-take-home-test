# Development Plan

My main focus will be **retrieval accuracy, reliable document parsing, and minimizing AI hallucinations**, rather than building a complex interface.

## 1. Implementation Plan

- **Document Parsing:** Use PyMuPDF to extract information from drilling report PDFs and python-docx to process the glossary. Convert the extracted information into structured JSON while preserving important metadata such as report dates, well names, and source pages.
- **Reusable Data Ingestion:** Build a simple ingestion script that can process additional PDFs with similar formats using a single command, without modifying the code.
- **Information Retrieval:** Implement BM25, keyword matching, and metadata filtering to retrieve the most relevant information. Add optional semantic reranking using OpenAI embeddings to improve retrieval for more complex questions.
- **AI Answer Generation:** Use OpenAI GPT-4o-mini to generate answers based only on retrieved information. For straightforward factual questions, retrieve answers directly from structured data where possible.
- **Source Attribution:** Include document names and page references in the answers so users can verify the information.
- **Out-of-Scope Handling:** Implement consistent refusal responses when the requested information is not available in the documents.
- **Chat Interface:** Build a minimal web interface using FastAPI with basic HTML and JavaScript, keeping most development effort focused on the AI and retrieval components.
- **Testing & Evaluation:** Use automated tests and sample questions to evaluate retrieval accuracy, response latency, source correctness, and out-of-scope handling.

## 2. Tech Stack & Libraries

- **Python:** Main programming language for backend development and data processing.
- **FastAPI:** REST API and backend service.
- **HTML + JavaScript:** Minimal chat interface.
- **PyMuPDF:** PDF text extraction.
- **python-docx:** DOCX glossary parsing.
- **JSON:** Storage for structured document data.
- **BM25:** Keyword-based retrieval and relevance ranking.
- **OpenAI GPT-4o-mini:** LLM for answer generation.
- **OpenAI text-embedding-3-small:** Optional semantic reranking.
- **OpenAI Python SDK:** Integration with OpenAI models.
- **Pydantic:** API request validation.
- **Uvicorn:** Application server.
- **python-dotenv:** API key and environment configuration.
- **Pytest + HTTPX:** Automated testing and API testing.

## 3. Technical Approach

I plan to use a **lightweight hybrid retrieval approach**, combining structured field matching, BM25, bilingual keyword matching, metadata filtering, and optional semantic reranking.

I will avoid unnecessary frameworks such as LangChain and external vector databases because the dataset is relatively small. This should keep the application simple, fast, maintainable, and easy to run locally.

## 4. Expected Outcome

The final MVP should be able to:

- Accurately answer questions based on the provided drilling reports and glossary.
- Support English and Indonesian queries.
- Provide traceable source references.
- Reject questions outside the available knowledge base.
- Process new reports with similar formats through a reusable ingestion pipeline.
- Run locally with straightforward setup instructions.
- Demonstrate retrieval performance through measurable accuracy and latency evaluations.

## 5. Work Tracking

- **Done:** Implementation and its required validation are complete.
- **In progress:** Development has started but the feature is not complete.
- **To do:** Required work that has not started yet.
- **Backlog:** Optional or future work that is not required for the first working version.

| Priority | Requirement | Status | Planned result |
|---|---|---|---|
| P0 | Parse DGOS, DDR, and glossary documents | In progress | Parser implementation is complete; functional and integration validation are still pending. |
| P0 | Reusable one-command ingestion | In progress | The ingestion command is implemented; runtime validation with PyMuPDF and sample documents is still pending. |
| P0 | Accurate document-grounded answers | To do | Answer from retrieved evidence and prefer structured facts for direct questions. |
| P0 | Out-of-scope refusal | To do | Return a consistent refusal when the documents do not contain an answer. |
| P0 | Source attribution | To do | Return document names, pages, sections, and report dates with answers. |
| P0 | Response time of no more than three minutes | To do | Measure end-to-end latency and keep every chat response within the required limit. |
| P0 | From-scratch setup documentation | In progress | Document prerequisites, installation, configuration, ingestion, startup, and testing. |
| P1 | Optional semantic embeddings | In progress | Cache building, cache loading, and question embedding are implemented; integration validation is still pending. |
| P1 | Retrieval evaluation | To do | Measure Top-1 accuracy, Recall@3, refusal accuracy, source correctness, and latency using labeled questions. |
| P1 | English and Indonesian queries | To do | Support bilingual keywords and natural-language questions. |
| P1 | Resolution documentation | To do | Record challenges, implemented solutions, known limitations, and future improvements. |
| P2 | SQLite storage | Backlog | Optionally store parsed results in SQLite without requiring an external service. JSON remains the MVP storage format. |
| P2 | PostgreSQL or another external database | Backlog | Only consider this with Docker Compose and simple reviewer setup instructions. |

The P0 requirements are necessary for the MVP. P1 items improve evaluation quality and documentation. P2 items are optional enhancements and should not delay the required functionality.
