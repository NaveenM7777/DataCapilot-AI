# DataCapilot AI

**AI Powered Data Assistant** — ask questions in plain English and get answers from a live SQL database, a company spreadsheet, and a company PDF report, either individually or combined by an orchestrating AI Agent.

**Live demo:** https://datacapilotai-genai-businesscapilot.streamlit.app/

---

## Overview

DataCapilot AI is a multi-agent Streamlit application that lets a non-technical user ask natural-language questions and get answers pulled from real data sources, with no need to write SQL, pandas code, or manually search a document.

The project is built in four phases, each accessible as its own tab:

| Tab | What it does |
|---|---|
| **SQL Assistant** | Converts a natural-language question into SQL, runs it against a live SQLite database (Chinook sample DB), and explains the result. |
| **Excel / CSV Agent** | Converts a natural-language question into pandas code, runs it against a company spreadsheet (multi-sheet support), and explains the result. |
| **PDF Agent** | Retrieves the most relevant sections of a company PDF report and answers questions using only that content, with page citations. |
| **AI Agent** | An orchestrator that decides — per question — which of the three tools above to call (one, two, or all three), runs them, and combines the results into a single answer. |

All four tabs work with **live data**: the SQL Assistant always queries the current state of the database, and the Excel/PDF Agents automatically detect when the underlying files change on disk and reload — no app restart required.

---

## Live Demo

**App URL:** https://datacapilotai-genai-businesscapilot.streamlit.app/

Try asking:
- *"How many albums does AC/DC have?"* (SQL Assistant)
- *"What was the total revenue for December?"* (Excel Agent)
- *"What's the return policy?"* (PDF Agent)
- *"Which city has our most expensive store?"* (AI Agent)

---

## Architecture

```
User question
     |
     v
Tab-specific handler (SQL / Excel / PDF)  --or--  AI Agent orchestrator
     |                                                  |
     v                                                  v
LLM generates SQL / pandas code /              LangGraph tool-calling agent
retrieves relevant PDF chunks                  picks 1-3 tools automatically
     |                                                  |
     v                                                  v
Executed safely (sandboxed exec,               Each tool runs the same
syntax-checked, read-only queries)             logic as the dedicated tabs
     |                                                  |
     v                                                  v
Result + plain-English explanation returned to the user
```

### Tech stack

- **Frontend / App framework:** Streamlit
- **LLM inference:** Groq API (Llama 3.3 70B for SQL/Excel/PDF generation, `openai/gpt-oss-120b` for AI Agent tool-calling reliability)
- **Agent orchestration:** LangChain + LangGraph (`create_react_agent`)
- **Database:** SQLite (Chinook sample database) via SQLAlchemy
- **Spreadsheet processing:** pandas, openpyxl
- **PDF processing:** pypdf, custom keyword-based chunk retriever (no external vector DB required)
- **Styling:** Custom CSS theme (navy/slate professional palette, no external UI framework)
- **Navigation:** `streamlit-option-menu`

---

## Project Structure

```
DATACAPILOT/
├── app.py                     # Main entry point, sidebar nav, live data preload
├── data/
│   ├── company_data.xlsx      # Sample multi-sheet spreadsheet (sales, stores, staff)
│   └── company_doc.pdf        # Sample company report PDF
├── database/
│   ├── db_connection.py       # SQLAlchemy engine setup
│   └── chinook.db             # Sample SQLite database
├── sql_agent/
│   ├── sql_generator.py       # NL question -> SQL via Groq
│   └── sql_executor.py        # Runs SQL, returns DataFrame
├── excel_agent/
│   ├── data_loader.py         # Loads spreadsheet (single sheet + all sheets), live-refresh aware
│   ├── code_generator.py      # NL question -> pandas code via Groq
│   └── code_executor.py       # Sandboxed execution with syntax + safety checks
├── pdf_agent/
│   ├── pdf_loader.py          # Extracts text, chunks it, live-refresh aware
│   ├── retriever.py           # Keyword-based relevant chunk retrieval
│   └── qa_generator.py        # Answers questions using retrieved chunks
├── ai_agent/
│   ├── tools.py                # LangChain @tool-wrapped versions of all three agents
│   └── orchestrator.py         # LangGraph agent that routes across tools
├── llm/
│   └── groq_client.py          # Shared Groq client helper
├── ui/
│   ├── theme.py                 # Custom CSS (navy/slate professional theme)
│   ├── sql_chat.py               # SQL Assistant tab UI
│   ├── excel_chat.py             # Excel Agent tab UI
│   ├── pdf_chat.py               # PDF Agent tab UI
│   └── ai_chat.py                 # AI Agent tab UI
├── requirements.txt
└── .env                        # GROQ_API_KEY (never committed — see .gitignore)
```

---

## Features

- **Natural language to SQL** with chat history context (follow-up questions like "now show only customers from Brazil" work correctly)
- **Natural language to pandas** with multi-sheet awareness — the AI Agent can pull from Monthly Sales, Store Locations, and Employee Performance sheets in a single answer
- **PDF question answering** with page-level citations, using a lightweight keyword retriever (no external vector database dependency)
- **Multi-tool orchestration** — a single AI Agent question can combine data from the SQL database, the spreadsheet, and the PDF report in one answer
- **Live data refresh** — SQL queries always hit the current database state; Excel/PDF files are automatically reloaded when changed on disk, without restarting the app
- **Safety guardrails**
  - Generated pandas code is syntax-validated before execution and run in a restricted sandbox (no imports, no file I/O, no `exec`/`eval` inside generated code, plotting calls blocked)
  - Generated SQL and pandas code failures return clear, actionable error messages instead of crashing
  - LLM tool-calling failures (a known Groq/Llama reliability issue) are caught and retried, with a deterministic keyword-based fallback router as a last resort
- **Automatic visualizations** — numeric results are automatically charted with `st.bar_chart` when relevant
- **CSV export** of any query result
- **Clean, professional UI** — custom dark navy/slate theme, no default Streamlit styling, no emoji clutter

---

## Setup and Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/NaveenM7777/DataCapilot-AI.git
cd DataCapilot-AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 5. Confirm sample data is in place

```
data/company_data.xlsx
data/company_doc.pdf
database/chinook.db
```

These are included in the repository — no manual setup needed for the demo data.

### 6. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Deployment (Streamlit Community Cloud)

This app is deployed on [Streamlit Community Cloud](https://share.streamlit.io):

1. Push the repository to GitHub (ensure `.env` is excluded via `.gitignore`)
2. On Streamlit Cloud, create a new app pointing at `app.py` on the `main` branch
3. Add the Groq API key under **Advanced settings → Secrets**:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
4. Deploy — Streamlit Cloud auto-redeploys on every push to `main`

**Live app:** https://datacapilotai-genai-businesscapilot.streamlit.app/

---

## Example Questions to Try

**SQL Assistant**
- How many albums does AC/DC have?
- Show the top 5 customers by total purchase amount.

**Excel / CSV Agent**
- What was the total revenue for December?
- Which store has the highest rent?

**PDF Agent**
- What's the return policy?
- How long is customer data retained?

**AI Agent (multi-source)**
- Which city has our most expensive store?
- Compare December's revenue in the spreadsheet to the report's outlook.
- Compare the employees in the spreadsheet to the employees in the database — are they the same people?

---

## Quality Engineering

![tests](https://github.com/NaveenM7777/DataCapilot-AI/actions/workflows/tests.yml/badge.svg?branch=main)

This project is also a quality-engineering case study. An automated suite checks the app at every level and runs on every push with GitHub Actions, with no secrets and no real AI calls.

| Level | What is checked |
|---|---|
| API | A FastAPI layer (`api/`) wraps the four agents: input validation, error handling, odd input, concurrent requests |
| AI answers | 28 golden questions with known answers, including checks that the orchestrator picks the right tool |
| Answer quality | DeepEval faithfulness and relevancy scores for the PDF agent, with a Groq model as the judge |
| Safety | SQL attacks, AI-written-code sandbox escapes, prompt injection, key leaks, personal data |
| UI | Streamlit AppTest and Playwright browser tests, with fake AI answers so they are free and repeatable |
| Performance | Latency report and concurrent-request tests |

Bugs the tests found, now fixed: the SQL safety check blocked harmless queries (the genre "Alternative" contains the letters ALTER); AI-written pandas code could escape its sandbox and read or write files; customer contact details could be queried freely; the UI named the wrong AI model.

Run the free tests with `pytest -v`. Full guide: [docs/TESTING.md](docs/TESTING.md). One-page summary: [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md).

New folders: `api/` (FastAPI layer), `tests/` (all tests, `tests/ui/` for the UI), `evals/` (DeepEval judge), `docs/`, `.github/workflows/` (CI).

## Known Limitations

- The PDF retriever uses keyword matching rather than semantic embeddings — works well for short, clearly-worded documents like the sample report, but would need an embeddings-based retriever for longer or more ambiguous documents.
- The sample SQLite database (Chinook) and the sample company spreadsheet/PDF are illustrative demo data, not connected to a real production system. See "Connecting to a Real Database" below for what's required to point this at live company data.
- LLM tool-calling on Groq's `llama-3.3-70b-versatile` occasionally produces malformed function-call output — this is a documented issue with that model on Groq's platform, handled here via automatic retry and a keyword-based fallback router, but not eliminated entirely.

---

## Connecting to a Real Database (Production Notes)

To point the SQL Assistant at a real company database instead of the sample Chinook DB:

1. Set `DATABASE_URL` in `.env` (or Streamlit Cloud secrets) to your database's connection string, e.g.:
   ```
   DATABASE_URL=postgresql://readonly_user:password@host:5432/dbname
   ```
2. **Use a read-only database user** — this is the most important production safety step. The app should never have write access to a real database.
3. The app already includes query-safety checks that block non-`SELECT` statements and cap result size, as an additional layer of protection.

Excel and PDF sources can similarly be pointed at any real company file by replacing `data/company_data.xlsx` and `data/company_doc.pdf` — the live-refresh logic will pick up changes automatically without a restart.

---

## Tech Notes / Design Decisions

- **Why LangGraph instead of a hand-rolled tool-calling loop:** an earlier version of the AI Agent manually managed the Groq tool-calling loop; it was migrated to LangGraph's `create_react_agent` for more robust handling of malformed tool-call responses (`handle_parsing_errors` equivalent) without maintaining custom retry logic.
- **Why a keyword retriever instead of embeddings for the PDF Agent:** keeps the stack dependency-light (no vector database required) while still being accurate for a short, well-structured document — a reasonable tradeoff for this project's scope.
- **Why sandboxed `exec()` for pandas code instead of a safer alternative:** the sandbox restricts available builtins, blocks imports/file I/O/plotting, and validates syntax before execution, balancing flexibility (arbitrary pandas operations) against safety for a demo environment.

---

## Author

Built by Naveen M — [GitHub](https://github.com/NaveenM7777)
