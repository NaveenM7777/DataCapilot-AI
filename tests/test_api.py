# ---------- Health ----------

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- SQL ----------

def test_sql_query_returns_answer(client, monkeypatch):
    def fake_agent(question):
        return {
            "sql": "SELECT COUNT(*) FROM customers;",
            "answer": "There are 42 customers.",
        }

    monkeypatch.setattr("api.main.ask_sql_agent", fake_agent)

    response = client.post("/sql/query", json={"question": "How many customers?"})

    assert response.status_code == 200
    assert response.json() == {
        "question": "How many customers?",
        "sql": "SELECT COUNT(*) FROM customers;",
        "answer": "There are 42 customers.",
    }


def test_sql_query_rejects_empty_question(client):
    response = client.post("/sql/query", json={"question": ""})
    assert response.status_code == 422


def test_sql_query_rejects_missing_question(client):
    response = client.post("/sql/query", json={})
    assert response.status_code == 422


def test_sql_query_handles_agent_failure(client, monkeypatch):
    def broken_agent(question):
        raise RuntimeError("database offline")

    monkeypatch.setattr("api.main.ask_sql_agent", broken_agent)

    response = client.post("/sql/query", json={"question": "hello"})

    assert response.status_code == 500
    assert "database offline" in response.json()["detail"]


# ---------- Excel ----------

def test_excel_analyze_returns_answer(client, monkeypatch):
    monkeypatch.setattr(
        "api.main.ask_excel_agent",
        lambda content, filename, question: {"answer": "Total is 3."},
    )
    response = client.post(
        "/excel/analyze",
        files={"file": ("sales.csv", b"a,b\n1,2", "text/csv")},
        data={"question": "What is the total?"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "filename": "sales.csv",
        "question": "What is the total?",
        "answer": "Total is 3.",
    }


def test_excel_analyze_rejects_wrong_file_type(client):
    response = client.post(
        "/excel/analyze",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"question": "anything"},
    )
    assert response.status_code == 400


def test_excel_analyze_requires_file(client):
    response = client.post("/excel/analyze", data={"question": "anything"})
    assert response.status_code == 422


# ---------- PDF ----------

def test_pdf_ask_returns_answer(client, monkeypatch):
    monkeypatch.setattr(
        "api.main.ask_pdf_agent",
        lambda content, filename, question: {"answer": "The refund window is 30 days."},
    )
    response = client.post(
        "/pdf/ask",
        files={"file": ("policy.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"question": "What is the refund window?"},
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "The refund window is 30 days."


def test_pdf_ask_rejects_wrong_file_type(client):
    response = client.post(
        "/pdf/ask",
        files={"file": ("sheet.xlsx", b"data", "application/octet-stream")},
        data={"question": "anything"},
    )
    assert response.status_code == 400