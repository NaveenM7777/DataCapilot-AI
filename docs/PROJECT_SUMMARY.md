# DataCapilot AI: Quality Engineering Case Study

**In one line:** an automated test suite for an LLM-powered data assistant (SQL, Excel and PDF agents plus an orchestrating AI agent), covering the API, answer accuracy, answer quality, safety, UI and performance, running on every push in CI.

## The problem

AI applications are hard to test: the same question can produce differently worded answers, an answer can sound confident and be wrong, and users can try to trick the system. A normal "assert the output equals X" test is not enough. This project shows a layered approach that tests the deterministic parts exactly and the AI parts with known answers, an AI judge and attack prompts.

## What was built

| Layer | Approach |
|---|---|
| API | A FastAPI layer wraps the four agents. pytest tests with mocked agents check validation, errors, odd input, concurrency and that no stack traces leak |
| AI answers | 28 golden questions with answers computed from the data, across all four agents. For the orchestrator the tests also check which tool it chose |
| Answer quality | DeepEval faithfulness and relevancy for the PDF agent, with a Groq model as the judge. The judge itself is tested first |
| Safety | SQL attacks, AI-written-code sandbox escapes, prompt injection, API-key leaks, personal data |
| UI | Streamlit AppTest (no browser) and Playwright (real browser), using a launcher that replaces the AI with fixed answers |
| Performance | Latency report for the SQL agent and a 40-request concurrency test |
| CI | GitHub Actions, two jobs, no secrets and no real AI calls |

## Results

- About 130 automated tests run free and repeatably in CI (126 in the main job, 5 in the browser job).
- About 50 more tests use the real AI on demand: 28 golden questions, 12 safety attacks, live-server and latency checks, plus 7 DeepEval quality checks.
- Real-model runs: SQL golden questions 9 of 9, Excel 8 of 8, orchestrator 4 of 4 (including correct tool choice), AI-safety attacks 12 of 12.
- PDF golden questions: 6 of 7 on the first run. The one failure was a test bug (the model wrote an invisible non-breaking space inside "New York"), fixed by normalizing text.
- DeepEval on the PDF agent: faithfulness 1.0 on all 5 questions, relevancy between 0.67 and 1.0.
- SQL agent latency over 5 questions: median 0.55 s, 95th percentile 2.07 s (a small sample).

## Bugs and risks the tests found

| Finding | Result |
|---|---|
| The SQL safety check blocked harmless queries: the genre "Alternative" contains the letters ALTER | Fixed: whole-word matching, quoted text ignored |
| AI-written pandas code could escape its sandbox: it could reach the `os` module, read local files and write files | Fixed: the code is checked before it runs. Attacks and normal questions are both tested |
| Customer and employee emails, phones, faxes and addresses could be queried freely | Fixed: those columns and `SELECT *` on those tables are blocked |
| The UI named the wrong AI model | Fixed: a test compares the label with the model the code really uses |
| The PDF report says 712 new customers, the spreadsheet adds up to 732 | Open: tracked as a known failure |
| When a tool fails, the orchestrator quietly falls back to keyword routing and returns the error as a normal answer | Open: documented |

## Decisions and why

- **Mock the AI in API and UI tests.** Real calls are slow, cost quota and vary, which is wrong for testing behaviour.
- **Separate product failures from environment failures.** A dropped connection or rate limit is reported as skipped, never as a wrong answer.
- **An AI judge is noisy, so test it.** It once claimed a document said something it did not, then gave the same answer a perfect score. Failing scores are confirmed with a second try, and the relevancy threshold (0.6) is documented with its reason.
- **Strict expected failures.** Known bugs are tracked as strict `xfail`, so the suite stays green but the moment a bug is fixed the test says to remove the marker.
- **Test the tests.** The answer matcher has its own unit tests, and the judge has sanity tests before its scores are trusted.
- **Keep DeepEval in its own environment** so it cannot disturb the main one.

## Limitations and next steps

- The code check lowers risk but is not a full sandbox. The proper fix is a separate locked-down process with a time limit.
- Real-AI tests run each question once, so a pass is evidence, not proof. Repeated runs would give pass rates.
- DeepEval covers the PDF agent only. Ragas retrieval metrics, bias and toxicity checks, and a load-testing tool are not done.

## Tech stack

Python, pytest, FastAPI, httpx, Streamlit (AppTest), Playwright, DeepEval, GitHub Actions, Groq (gpt-oss-120b for the app, Qwen as the judge), SQLite, pandas.

## Run it

```
pytest -v
```

See `docs/TESTING.md` for every command and the full list of findings.