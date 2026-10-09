# Development Plan

## 1. Project Overview

I plan to build a lightweight AI chatbot that allows users to ask questions about Oil & Gas drilling reports in natural language, without having to manually read through technical documents.

The chatbot will support both English and Indonesian, provide answers based on the uploaded documents, and include source references.

My main focus will be **retrieval accuracy, reliable document parsing, and minimizing AI hallucinations**, rather than building a complex interface.

## 2. Implementation Plan

- **Document Parsing:** Use PyMuPDF to extract information from drilling report PDFs and python-docx to process the glossary. Convert the extracted information into structured JSON while preserving important metadata such as report dates, well names, and source pages.
- **Reusable Data Ingestion:** Build a simple ingestion script that can process additional PDFs with similar formats using a single command, without modifying the code.
- **Information Retrieval:** Implement BM25, keyword matching, and metadata filtering to retrieve the most relevant information. Add optional semantic reranking using OpenAI embeddings to improve retrieval for more complex questions.
- **AI Answer Generation:** Use OpenAI GPT-4o-mini to generate answers based only on retrieved information. For straightforward factual questions, retrieve answers directly from structured data where possible.
- **Source Attribution:** Include document names and page references in the answers so users can verify the information.
- **Out-of-Scope Handling:** Implement consistent refusal responses when the requested information is not available in the documents.
- **Chat Interface:** Build a minimal web interface using FastAPI with basic HTML and JavaScript, keeping most development effort focused on the AI and retrieval components.
- **Testing & Evaluation:** Use automated tests and sample questions to evaluate retrieval accuracy, response latency, source correctness, and out-of-scope handling.

## 3. Tech Stack & Libraries

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

## 4. Technical Approach

I plan to use a **lightweight hybrid retrieval approach**, combining structured field matching, BM25, bilingual keyword matching, metadata filtering, and optional semantic reranking.

I will avoid unnecessary frameworks such as LangChain and external vector databases because the dataset is relatively small. This should keep the application simple, fast, maintainable, and easy to run locally.

## 5. Expected Outcome

The final MVP should be able to:

- Accurately answer questions based on the provided drilling reports and glossary.
- Support English and Indonesian queries.
- Provide traceable source references.
- Reject questions outside the available knowledge base.
- Process new reports with similar formats through a reusable ingestion pipeline.
- Run locally with straightforward setup instructions.
- Demonstrate retrieval performance through measurable accuracy and latency evaluations.
