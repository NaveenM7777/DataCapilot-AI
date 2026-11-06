import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"

# (url, a question that agent can really answer)
REAL_QUESTIONS = [
    ("/sql/query", "How many customers are there?"),
    ("/excel/query", "What is the total revenue?"),
    ("/pdf/query", "What is the return window for physical media?"),
    ("/agent/query", "How many customers are there?"),
]
URLS = [item[0] for item in REAL_QUESTIONS]
IDS = ["sql", "excel", "pdf", "agent"]


@pytest.fixture(scope="module")
def live():
    client = httpx.Client(base_url=BASE_URL, timeout=120)
    try:
        client.get("/health")
    except httpx.ConnectError:
        pytest.skip("Live server is not running (uvicorn api.main:app --reload)")
    return client


def test_live_health(live):
    response = live.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("url", URLS, ids=IDS)
def test_live_rejects_empty_question(live, url):
    response = live.post(url, json={"question": ""})
    assert response.status_code == 422


@pytest.mark.llm
@pytest.mark.parametrize("url,question", REAL_QUESTIONS, ids=IDS)
def test_live_returns_real_answer(live, url, question):
    response = live.post(url, json={"question": question})
    assert response.status_code == 200, response.text
    assert response.json()["answer"].strip() != ""