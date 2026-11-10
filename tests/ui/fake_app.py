"""
Test-only launcher for the Streamlit app.

It replaces the AI calls with fixed answers, so UI tests are free, fast and
give the same result every time. Everything else (the real screens, the real
database) is the real app.

Used by:
  - tests/ui/test_ui_apptest.py  (Streamlit's built-in test runner, no browser)
  - tests/ui/test_ui_browser.py  (Playwright, real browser)
"""
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)  # the app uses relative paths such as database/chinook.db
sys.path.insert(0, str(ROOT))

# The agents need *a* key to be imported, but with the fakes below no real call is made.
os.environ.setdefault("GROQ_API_KEY", "fake-key-for-ui-tests")

FAKE_SQL = "SELECT COUNT(*) AS customers FROM Customer"
FAKE_EXPLANATION = "Counts every row in the Customer table."
FAKE_AGENT_ANSWER = "There are 59 customers."

import ai_agent.orchestrator as orchestrator  # noqa: E402
import llm.groq_client as groq_client  # noqa: E402
import sql_agent.sql_generator as sql_generator  # noqa: E402

sql_generator.generate_sql = lambda question, history=None: FAKE_SQL
groq_client.explain_sql = lambda sql_query: FAKE_EXPLANATION
orchestrator.run_agent = lambda question, history=None: {
    "answer": FAKE_AGENT_ANSWER,
    "tools_used": ["query_database"],
    "steps": [
        {"tool": "query_database", "result": {"content": "customers\n59"}},
    ],
}

# AppTest cannot click the sidebar menu (it is a custom component), so tests can
# pick the screen with an environment variable. Browser tests do not set it and
# use the real menu.
screen = os.environ.get("DATACAPILOT_TEST_SCREEN")
if screen:
    import streamlit_option_menu

    streamlit_option_menu.option_menu = lambda *args, **kwargs: screen

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
