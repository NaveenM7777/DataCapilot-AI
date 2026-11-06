import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="module")
def live():
    client = httpx.Client(base_url=BASE_URL, timeout=30)
    try:
        client.get("/health")
    except httpx.ConnectError:
        pytest.skip("Live server is not running (uvicorn api.main:app --reload)")
    return client


def test_live_health(live):
    r = live.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_live_sql_valid(live):
    r = live.post("/sql/query", json={"question": "How many customers?"})
    assert r.status_code == 200
    assert {"question", "sql", "answer"} <= set(r.json())


def test_live_sql_empty_question(live):
    r = live.post("/sql/query", json={"question": ""})
    assert r.status_code == 422


def test_live_excel_valid(live):
    r = live.post(
        "/excel/analyze",
        files={"file": ("sales.csv", b"a,b\n1,2", "text/csv")},
        data={"question": "What is the total?"},
    )
    assert r.status_code == 200
    assert "answer" in r.json()


def test_live_excel_wrong_type(live):
    r = live.post(
        "/excel/analyze",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"question": "anything"},
    )
    assert r.status_code == 400


def test_live_pdf_valid(live):
    r = live.post(
        "/pdf/ask",
        files={"file": ("policy.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"question": "What is the refund window?"},
    )
    assert r.status_code == 200
    assert "answer" in r.json()


def test_live_pdf_wrong_type(live):
    r = live.post(
        "/pdf/ask",
        files={"file": ("sheet.xlsx", b"data", "application/octet-stream")},
        data={"question": "anything"},
    )
    assert r.status_code == 400