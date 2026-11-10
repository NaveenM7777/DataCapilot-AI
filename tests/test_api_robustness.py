import pytest

URLS = ["/sql/query", "/excel/query", "/pdf/query", "/agent/query"]
IDS = ["sql", "excel", "pdf", "agent"]

UNUSUAL_QUESTIONS = {
    "sql-injection-text": "'; DROP TABLE Customer; --",
    "html-tags": "<script>alert(1)</script>",
    "emoji-and-unicode": "emoji \U0001F600 and \u65e5\u672c\u8a9e text",
    "newlines-and-tabs": "line1\nline2\ttabbed",
    "null-character": "null char \u0000 inside",
    "longest-allowed": "a" * 1000,
}


@pytest.mark.parametrize(
    "question", UNUSUAL_QUESTIONS.values(), ids=UNUSUAL_QUESTIONS.keys()
)
def test_unusual_text_is_handled_safely(client, monkeypatch, question):
    monkeypatch.setattr(
        "api.main.ask_sql_agent", lambda q: {"sql": "SELECT 1", "answer": q}
    )

    response = client.post("/sql/query", json={"question": question})

    assert response.status_code == 200
    assert response.json()["question"] == question


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_invalid_json_body_is_rejected(client, url):
    response = client.post(
        url, content="{this is not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 422


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_wrong_content_type_is_rejected(client, url):
    response = client.post(
        url, content="question=hello", headers={"content-type": "text/plain"}
    )
    assert response.status_code == 422


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_question_must_be_text(client, url):
    response = client.post(url, json={"question": 12345})
    assert response.status_code == 422


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_get_is_not_allowed_on_query_endpoints(client, url):
    response = client.get(url)
    assert response.status_code == 405


def test_unknown_route_returns_404(client):
    response = client.get("/admin")
    assert response.status_code == 404


def test_unknown_extra_fields_are_ignored(client, monkeypatch):
    monkeypatch.setattr(
        "api.main.ask_sql_agent", lambda q: {"sql": "SELECT 1", "answer": "ok"}
    )

    response = client.post("/sql/query", json={"question": "hi", "is_admin": True})

    assert response.status_code == 200


def test_server_errors_do_not_leak_stack_traces(client, monkeypatch):
    def broken(question):
        raise RuntimeError("boom")

    monkeypatch.setattr("api.main.ask_sql_agent", broken)

    response = client.post("/sql/query", json={"question": "hi"})

    assert response.status_code == 500
    assert "Traceback" not in response.text
    assert 'File "' not in response.text