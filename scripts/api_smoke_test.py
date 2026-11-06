import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"

results = []


def check(name, condition):
    results.append(condition)
    print(("PASS" if condition else "FAIL"), "-", name)


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=30)

    try:
        r = client.get("/health")
    except httpx.ConnectError:
        print("Cannot reach the server. Start it first with:")
        print("  uvicorn api.main:app --reload")
        sys.exit(1)

    check("health returns 200", r.status_code == 200)
    check("health body is ok", r.json() == {"status": "ok"})

    r = client.post("/sql/query", json={"question": "How many customers?"})
    check("sql valid question returns 200", r.status_code == 200)
    body = r.json()
    check("sql response has question, sql, answer",
          all(k in body for k in ("question", "sql", "answer")))

    r = client.post("/sql/query", json={"question": ""})
    check("sql empty question returns 422", r.status_code == 422)

    r = client.post(
        "/excel/analyze",
        files={"file": ("sales.csv", b"a,b\n1,2", "text/csv")},
        data={"question": "What is the total?"},
    )
    check("excel valid file returns 200", r.status_code == 200)
    check("excel response has answer", "answer" in r.json())

    r = client.post(
        "/excel/analyze",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"question": "anything"},
    )
    check("excel wrong file type returns 400", r.status_code == 400)

    r = client.post(
        "/pdf/ask",
        files={"file": ("policy.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"question": "What is the refund window?"},
    )
    check("pdf valid file returns 200", r.status_code == 200)
    check("pdf response has answer", "answer" in r.json())

    r = client.post(
        "/pdf/ask",
        files={"file": ("sheet.xlsx", b"data", "application/octet-stream")},
        data={"question": "anything"},
    )
    check("pdf wrong file type returns 400", r.status_code == 400)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()