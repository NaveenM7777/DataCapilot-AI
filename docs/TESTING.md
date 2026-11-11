# Testing DataCapilot-AI

An automated test suite around the SQL, Excel, PDF and AI-orchestrator agents and the Streamlit app. It checks that the API behaves, that the AI gives correct and well-supported answers, that the system resists misuse, and that the screens work in a real browser.

## Test layers

| Layer | Files | Real AI? | Where it runs |
|---|---|---|---|
| API behaviour | `tests/test_api.py` | No (mocked) | Everywhere, CI |
| API robustness | `tests/test_api_robustness.py` | No | Everywhere, CI |
| SQL safety and personal data | `tests/test_sql_validator.py`, `tests/test_safety_sql.py` | No | Everywhere, CI |
| Code-execution safety | `tests/test_safety_excel_sandbox.py` | No | Everywhere, CI |
| Answer matching | `tests/test_answer_matching.py` | No | Everywhere, CI |
| Model name in one place | `tests/test_model_config.py` | No | Everywhere, CI |
| Data consistency | `tests/test_data_consistency.py` | No | Everywhere, CI (the company files are in the repository) |
| API performance | `tests/test_performance.py` | Mostly no | Everywhere, CI |
| UI screens (no browser) | `tests/ui/test_ui_apptest.py` | No (fake AI) | Everywhere, CI |
| UI in a real browser | `tests/ui/test_ui_browser.py` | No (fake AI) | Needs Playwright, CI browser job |
| Live server | `tests/test_live_api.py` | Optional | Server running |
| Golden questions | `tests/test_golden.py` | Yes (`llm`) | Manual |
| AI safety | `tests/test_safety_llm.py` | Yes (`llm`) | Manual |
| Answer quality (DeepEval) | `tests/test_llm_deepeval.py` | Yes, AI judge (`llm`) | Manual, `venv-eval` |

Tests marked `llm` call the real Groq API. They are skipped by default so normal runs are free, fast and repeatable. Network and rate-limit problems are reported as skips, never as wrong answers.

## Environments

- **venv** (normal): `pip install -r requirements.txt -r requirements-quality.txt`. For browser tests also `pip install -r requirements-ui.txt` and `playwright install chromium`.
- **venv-eval**: the same packages plus `-r requirements-eval.txt` (DeepEval). It is separate so DeepEval cannot disturb the main environment.
- **.env**: `GROQ_API_KEY` is required for real-AI tests. `GROQ_JUDGE_MODEL` is optional (default `qwen/qwen3.8-27b`).

## How to run

```
pytest -v                                        # everything free
pytest tests/ui/test_ui_apptest.py -v            # screens, no browser
pytest tests/ui/test_ui_browser.py -v            # real browser (HEADED: $env:HEADED="1")

pytest -m llm tests/test_golden.py -k sql        # real AI, one agent at a time
pytest -m llm tests/test_golden.py -k excel
pytest -m llm tests/test_golden.py -k "pdf- or admits"
pytest -m llm tests/test_golden.py -k orchestrator
pytest -m llm tests/test_safety_llm.py -rs       # AI safety
pytest -m llm tests/test_performance.py -s       # latency report in reports/performance/

pytest -m llm tests/test_llm_deepeval.py -v -rs  # in venv-eval; scores in reports/llm/
uvicorn api.main:app                             # then: pytest tests/test_live_api.py -v
```

Expected totals for `pytest -v`: 132 passed, 6 skipped, 45 deselected, 1 xfailed (Playwright installed). GitHub CI main job: 127 passed, 7 skipped, 45 deselected, 1 xfailed. GitHub CI browser job: 5 passed.

## How the UI tests avoid the real AI

`tests/ui/fake_app.py` starts the real app with the AI calls replaced by fixed answers. The screens, the database and the layout are real, so the UI tests are free and repeatable. The AppTest tests also remove and restore the app's modules around each test so the fakes can never leak into other tests. A failed browser test saves a screenshot in `reports/ui/`.

## Findings so far

| # | Finding | Status |
|---|---|---|
| 1 | The SQL validator blocked harmless queries containing the genre "Alternative" (it contains the letters ALTER) | Fixed, covered by tests |
| 2 | The Excel agent's `exec()` sandbox could be escaped: AI-written code could reach `os`, read local files and write files | Fixed with a pre-run code check, covered by tests |
| 3 | The PDF report says 712 new customers, the spreadsheet adds up to 732 | Open (tracked as `xfail`) |
| 4 | Customer and employee emails, phones, faxes and addresses could be queried without restriction | Fixed: those columns and SELECT * on the Customer and Employee tables are blocked, covered by tests |
| 5 | When a tool fails, the orchestrator silently falls back to keyword routing and returns the error text as an HTTP 200 answer | Open (observation) |
| 6 | Models write look-alike characters (non-breaking spaces and hyphens), which broke exact text matching | Fixed in the test helpers |
| 7 | The AI judge is noisy: it once claimed the PDF names Toronto as the oldest store, then scored the same answer 1.0 | Mitigated: a failing score is confirmed with a second try, and the relevancy threshold (0.6) is documented |
| 8 | The UI showed "Llama 3.3" while every agent uses gpt-oss-120b | Fixed, test now guards it |
| 9 | The model name was hard-coded in 8 places across 5 files | Fixed: one constant in `llm/config.py`, and a test fails if a model name is typed into the code again |
| 10 | The first screen of a fresh session takes more than 5 seconds to appear | Open (observation) |

## Known limitations

- The code check lowers risk but is not a full sandbox. Running AI-written code in a separate locked-down process with a time limit is the proper fix. Code that never finishes (a huge calculation) is not covered.
- The personal-data guard blocks contact-detail columns by name. Names and other business data stay available by design.
- Golden tests match facts (numbers and key words). Answer quality is scored by DeepEval for the PDF agent only.
- Real-AI tests run each question once. A pass is evidence, not proof, and AI answers can vary between runs.
- The UI tests use fake AI answers, so the link between the screens and the real AI is covered by the API and golden tests, not by the UI tests.
- The browser tests use Chromium only.

## Continuous integration

`.github/workflows/tests.yml` runs two jobs on every push and pull request, with no secrets and no real AI calls: the free test suite (with an HTML report) and the browser tests (with screenshots if one fails).