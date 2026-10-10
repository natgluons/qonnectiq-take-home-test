"""Minimal HTTP API + browser interface. Run: uvicorn app:app --reload"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from qa import answer
from retrieval import load_corpus

load_dotenv()
app = FastAPI(title="Well Report AI", version="1.0.0")
ROOT = Path(__file__).resolve().parent


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/")
def home():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/app.js")
def javascript():
    return FileResponse(ROOT / "web" / "app.js", media_type="application/javascript")


@app.get("/api/health")
def health():
    corpus = load_corpus(os.getenv("PARSED_DATA_DIR", "parsed_data"))
    return {"documents": len(corpus), "ready": bool(corpus)}


@app.post("/api/chat")
def chat(request: ChatRequest):
    # Reload the JSON each request: a newly ingested PDF is immediately searchable
    # without a server restart or an extra database / indexing service.
    corpus = load_corpus(os.getenv("PARSED_DATA_DIR", "parsed_data"))
    if not corpus:
        raise HTTPException(503, "No documents indexed. Run: python ingest.py")
    try:
        response, sources = answer(request.question, corpus)
    except Exception as exc:
        # Never include the provider's raw error: it may reveal credentials.
        raise HTTPException(502, "Model API unavailable. Check OPENAI_API_KEY and model access.") from exc
    return {
        "answer": response,
        "sources": [
            {k: s.get(k) for k in ("source_file", "page", "section", "report_date", "score")}
            for s in sources
        ],
    }
