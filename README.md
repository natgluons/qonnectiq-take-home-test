# Well Report AI

A document-grounded chat application for well reports and an Oil & Gas glossary.

## Local setup

Prerequisites: Python 3.11 or newer and an OpenAI API key.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Keep source documents in `datasets/` and generated JSON in `parsed_data/`.
Credentials, source documents, and generated data are intentionally excluded from Git.
