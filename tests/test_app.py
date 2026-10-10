from fastapi.testclient import TestClient
from app import app


def test_health_and_chat(tmp_path, monkeypatch):
    from json import dumps
    (tmp_path / "sample.json").write_text(dumps({
        "document_type": "DGOS", "source_file": "fake.pdf", "report_number": 1,
        "report_date": "2026-01-01", "well_name": "EXAMPLE-1", "country": "EXAMPLELAND",
        "sections": [],
    }), encoding="utf8")
    monkeypatch.setenv("PARSED_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/api/health").json()["documents"] == 1
    data = client.post("/api/chat", json={"question": "Dimana letak lokasi sumur?"}).json()
    assert data["answer"] == "EXAMPLELAND"
    assert data["sources"][0]["source_file"] == "fake.pdf"
    assert "text" not in data["sources"][0]  # Don't expose raw retrieved content.


def test_health_and_chat_with_sqlite(tmp_path, monkeypatch):
    from storage import replace_corpus

    database = tmp_path / "corpus.db"
    replace_corpus(database, [{
        "document_type": "DGOS", "source_file": "sqlite.pdf", "report_number": 2,
        "report_date": "2026-01-02", "well_name": "EXAMPLE-2", "country": "MALAYSIA",
        "sections": [],
    }])
    monkeypatch.setenv("CORPUS_DATABASE", str(database))
    client = TestClient(app)
    assert client.get("/api/health").json()["documents"] == 1
    data = client.post("/api/chat", json={"question": "Dimana letak lokasi sumur?"}).json()
    assert data["answer"] == "MALAYSIA"
    assert data["sources"][0]["source_file"] == "sqlite.pdf"
