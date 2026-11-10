import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from api.main import app

load_dotenv()

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports" / "performance"


def percentile(values, fraction):
    ordered = sorted(values)
    index = max(0, int(round(fraction * len(ordered))) - 1)
    return ordered[index]


def test_health_endpoint_is_fast(client):
    durations = []
    for _ in range(100):
        start = time.perf_counter()
        response = client.get("/health")
        durations.append(time.perf_counter() - start)
        assert response.status_code == 200

    assert percentile(durations, 0.95) < 0.5, "95% of /health calls should take under 0.5 s"


def test_api_handles_concurrent_requests(monkeypatch):
    """The API layer itself (not the AI) must cope with many users at once."""

    def slow_but_fine(result):
        def agent(question):
            time.sleep(0.05)  # pretend the agent needs a moment
            return result

        return agent

    monkeypatch.setattr("api.main.ask_sql_agent", slow_but_fine({"sql": "SELECT 1", "answer": "ok"}))
    monkeypatch.setattr("api.main.ask_excel_agent", slow_but_fine({"code": "result = 1", "answer": "ok"}))
    monkeypatch.setattr("api.main.ask_pdf_agent", slow_but_fine({"answer": "ok", "pages": [1]}))
    monkeypatch.setattr(
        "api.main.ask_ai_agent", slow_but_fine({"answer": "ok", "tools_used": []})
    )

    urls = ["/sql/query", "/excel/query", "/pdf/query", "/agent/query"] * 10  # 40 requests

    def send(url):
        with TestClient(app) as client:
            return client.post(url, json={"question": "How many?"}).status_code

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=10) as pool:
        codes = list(pool.map(send, urls))
    elapsed = time.perf_counter() - start

    assert codes == [200] * 40
    assert elapsed < 10, f"40 requests took {elapsed:.1f} s"


QUESTIONS = [
    "How many customers are there?",
    "How many artists are there?",
    "How many albums are there?",
    "How many invoices are there?",
    "How many employees are there?",
]


@pytest.mark.llm
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY is not set")
def test_sql_agent_latency_report():
    from llm_helpers import ask

    durations = []
    for question in QUESTIONS:
        start = time.perf_counter()
        ask("sql", question)
        durations.append(time.perf_counter() - start)

    report = {
        "questions": len(durations),
        "median_seconds": round(statistics.median(durations), 2),
        "p95_seconds": round(percentile(durations, 0.95), 2),
        "slowest_seconds": round(max(durations), 2),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "sql_latency.json").write_text(json.dumps(report, indent=2))
    print("\nSQL agent latency:", report)

    assert report["p95_seconds"] < 30, f"SQL agent is too slow: {report}"