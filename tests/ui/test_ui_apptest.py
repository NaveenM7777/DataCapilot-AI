"""
UI tests that need NO browser: Streamlit's built-in AppTest runs the real app
screens in memory. The AI calls are replaced by tests/ui/fake_app.py, so these
tests are free and also run in CI.
"""
import re
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
FAKE_APP = str(ROOT / "tests" / "ui" / "fake_app.py")

FAKE_SQL = "SELECT COUNT(*) AS customers FROM Customer"
FAKE_AGENT_ANSWER = "There are 59 customers."

# Modules the app imports. They are removed before and after each test so the
# fake answers can never leak into other tests (for example the real-AI ones).
OWNED_PACKAGES = {"ui", "sql_agent", "llm", "ai_agent", "excel_agent", "pdf_agent", "database"}


@pytest.fixture(autouse=True)
def isolated_modules(monkeypatch):
    def owned(name):
        return name.split(".")[0] in OWNED_PACKAGES

    saved = {name: module for name, module in sys.modules.items() if owned(name)}
    for name in saved:
        del sys.modules[name]

    # A fresh import of the agents needs a key; the fakes mean it is never used.
    monkeypatch.setenv("GROQ_API_KEY", "fake-key-for-ui-tests")

    yield

    for name in [n for n in sys.modules if owned(n)]:
        del sys.modules[name]
    sys.modules.update(saved)


def open_app(monkeypatch, screen=None):
    if screen:
        monkeypatch.setenv("DATACAPILOT_TEST_SCREEN", screen)
    else:
        monkeypatch.delenv("DATACAPILOT_TEST_SCREEN", raising=False)
    app = AppTest.from_file(FAKE_APP, default_timeout=60)
    app.run()
    return app


def metric_value(app, label):
    return [m.value for m in app.metric if m.label == label]


# --- App start ---------------------------------------------------------------


def test_app_starts_without_errors(monkeypatch):
    app = open_app(monkeypatch)

    assert not app.exception
    assert app.title[0].value == "DataCapilot AI"


def test_sidebar_shows_database_and_model_boxes(monkeypatch):
    app = open_app(monkeypatch)

    assert "Chinook" in app.sidebar.success[0].value
    assert len(app.sidebar.info) == 1


def test_model_label_names_the_model_that_is_really_used(monkeypatch):
    code = (ROOT / "llm" / "config.py").read_text(encoding="utf-8")
    real_model = re.search(r'MODEL\s*=\s*"([^"]+)"', code).group(1)  # e.g. openai/gpt-oss-120b
    short_name = real_model.split("/")[-1]

    app = open_app(monkeypatch)

    def squash(text):
        # 'gpt-oss-120b' and 'GPT-OSS 120B' are the same model
        return re.sub(r"[^a-z0-9]", "", text.lower())

    assert squash(short_name) in squash(app.sidebar.info[0].value)
    assert squash(short_name) in squash(" ".join(metric_value(app, "Model")))


# --- SQL screen --------------------------------------------------------------


def test_sql_screen_warns_when_question_is_empty(monkeypatch):
    app = open_app(monkeypatch)

    app.button[0].click().run()

    assert [w.value for w in app.warning] == ["Please enter a question."]


def test_sql_question_shows_sql_and_result(monkeypatch):
    app = open_app(monkeypatch)

    app.text_input[0].input("How many customers are there?").run()
    app.button[0].click().run()

    assert not app.exception
    assert app.code[0].value == FAKE_SQL
    assert int(app.dataframe[0].value.iloc[0, 0]) == 59
    assert metric_value(app, "Questions") == ["1"]


def test_sql_screen_counts_every_question(monkeypatch):
    app = open_app(monkeypatch)

    for question in ("How many customers are there?", "How many customers are there today?"):
        app.text_input[0].input(question).run()
        app.button[0].click().run()

    assert metric_value(app, "Questions") == ["2"]


# --- AI Agent screen ---------------------------------------------------------


def test_ai_agent_screen_warns_when_question_is_empty(monkeypatch):
    app = open_app(monkeypatch, screen="AI Agent")

    app.button[0].click().run()

    assert [w.value for w in app.warning] == ["Please enter a question."]


def test_ai_agent_screen_shows_answer_and_tools_used(monkeypatch):
    app = open_app(monkeypatch, screen="AI Agent")

    app.text_input[0].input("How many customers are there?").run()
    app.button[0].click().run()

    assert not app.exception
    assert FAKE_AGENT_ANSWER in [box.value for box in app.info]
    assert "Tools used: Database" in [c.value for c in app.caption]


# --- Other screens -----------------------------------------------------------


@pytest.mark.parametrize(
    "screen,title",
    [("Excel Agent", "Excel / CSV Agent"), ("PDF Agent", "PDF Agent")],
)
def test_other_screens_open_without_errors(monkeypatch, screen, title):
    app = open_app(monkeypatch, screen=screen)

    assert not app.exception
    assert app.title[0].value == title
