import pytest

# (url, function to replace with a fake, fake agent result)
CASES = [
    (
        "/sql/query",
        "api.main.ask_sql_agent",
        {"sql": "SELECT COUNT(*) FROM Customer", "answer": "59"},
    ),
    (
        "/excel/query",
        "api.main.ask_excel_agent",
        {"code": "result = 272500", "answer": "272500"},
    ),
    (
        "/pdf/query",
        "api.main.ask_pdf_agent",
        {"answer": "30 days (Page 3)", "pages": [3]},
    ),
    (
        "/agent/query",
        "api.main.ask_ai_agent",
        {"answer": "There are 59 customers.", "tools_used": ["query_database"]},
    ),
]
URLS = [case[0] for case in CASES]
IDS = ["sql", "excel", "pdf", "agent"]


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("url,target,fake_result", CASES, ids=IDS)
def test_endpoint_returns_agent_answer(client, monkeypatch, url, target, fake_result):
    monkeypatch.setattr(target, lambda question: fake_result)

    response = client.post(url, json={"question": "test question"})

    assert response.status_code == 200
    assert response.json() == {"question": "test question", **fake_result}


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_endpoint_rejects_empty_question(client, url):
    response = client.post(url, json={"question": ""})
    assert response.status_code == 422


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_endpoint_rejects_whitespace_question(client, url):
    response = client.post(url, json={"question": "     "})
    assert response.status_code == 422


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_endpoint_rejects_missing_question(client, url):
    response = client.post(url, json={})
    assert response.status_code == 422


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_endpoint_rejects_too_long_question(client, url):
    response = client.post(url, json={"question": "a" * 1001})
    assert response.status_code == 422


@pytest.mark.parametrize("url,target,fake_result", CASES, ids=IDS)
def test_endpoint_handles_agent_failure(client, monkeypatch, url, target, fake_result):
    def broken_agent(question):
        raise RuntimeError("boom")

    monkeypatch.setattr(target, broken_agent)

    response = client.post(url, json={"question": "hello"})

    assert response.status_code == 500
    assert "boom" in response.json()["detail"]