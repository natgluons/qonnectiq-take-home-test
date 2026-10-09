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
