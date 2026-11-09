"""
Real-browser UI tests with Playwright. The app runs with fake AI answers
(tests/ui/fake_app.py), so these tests are free and repeatable.

Needs:  pip install playwright   and   playwright install chromium
Without Playwright this whole file is skipped.

Handy options:
  HEADED=1 pytest tests/ui/test_ui_browser.py        (watch the browser)
Failed tests save a screenshot in reports/ui/
"""
import pytest

pytest.importorskip("playwright.sync_api", reason="Playwright is not installed")

from playwright.sync_api import expect  # noqa: E402

# The app runs its whole script (imports, loading the Excel and PDF) for every
# new browser session, which can take 10+ seconds on a slower machine.
# Playwright's default of 5 seconds for expect() is too short.
expect.set_options(timeout=45_000)

FAKE_SQL = "SELECT COUNT(*) AS customers FROM Customer"
FAKE_EXPLANATION = "Counts every row in the Customer table."
FAKE_AGENT_ANSWER = "There are 59 customers."

MENU_ITEMS = ["SQL Assistant", "Excel Agent", "PDF Agent", "AI Agent"]


def sidebar_menu(page):
    """The sidebar menu is a custom component, so it lives inside an iframe."""
    return page.frame_locator("iframe[title*='option_menu']")


def open_app(page, app_url):
    page.goto(app_url)
    expect(page.get_by_role("heading", name="DataCapilot AI").first).to_be_visible()


def ask(page, label, question, button):
    box = page.get_by_label(label)
    box.fill(question)
    box.press("Enter")  # Streamlit sends the text when you press Enter
    page.get_by_role("button", name=button).click()


def test_home_page_loads(page, app_url):
    open_app(page, app_url)

    expect(page).to_have_title("DataCapilot AI")
    expect(page.get_by_text("Ask questions about your SQLite database in plain English.")).to_be_visible()


def test_sidebar_menu_lists_all_agents(page, app_url):
    open_app(page, app_url)

    menu = sidebar_menu(page)
    for item in MENU_ITEMS:
        expect(menu.get_by_text(item)).to_be_visible()


def test_sql_empty_question_shows_a_warning(page, app_url):
    open_app(page, app_url)

    page.get_by_role("button", name="Generate SQL").click()

    expect(page.get_by_text("Please enter a question.")).to_be_visible()


def test_sql_question_shows_sql_and_explanation(page, app_url):
    open_app(page, app_url)

    ask(page, "Ask your question:", "How many customers are there?", "Generate SQL")

    expect(page.get_by_text(FAKE_SQL)).to_be_visible()
    expect(page.get_by_text(FAKE_EXPLANATION)).to_be_visible()
    expect(page.get_by_role("button", name="Download CSV")).to_be_visible()


def test_user_can_switch_to_the_ai_agent_and_ask(page, app_url):
    open_app(page, app_url)

    sidebar_menu(page).get_by_text("AI Agent").click()
    expect(page.get_by_role("heading", name="AI Agent", exact=True)).to_be_visible()

    ask(
        page,
        "Ask anything about your database, spreadsheet, or PDF:",
        "How many customers are there?",
        "Ask Agent",
    )

    expect(page.get_by_text(FAKE_AGENT_ANSWER)).to_be_visible()
    expect(page.get_by_text("Tools used: Database")).to_be_visible()
