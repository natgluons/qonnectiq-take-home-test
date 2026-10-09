# Qonnectiq Take Home Test

### Project Overview
Lightweight AI chatbot that allows users to ask questions about Oil & Gas drilling reports in natural language, without having to manually read through technical documents. The chatbot will support both English and Indonesian, provide answers based on the uploaded documents, and include source references.

#### **Important Note:** Development Plan (stacks used, expected outcomes, work tracking & priorities for the MVP, etc) are explained in development_plan.md

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
OPENAI_API_KEY=your-openai-api-key
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

Not yet available.

### Run the Chat Application

Not yet available.

### Run Tests and Evaluation

Not yet available.
