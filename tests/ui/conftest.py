import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FAKE_APP = ROOT / "tests" / "ui" / "fake_app.py"
SCREENSHOT_DIR = ROOT / "reports" / "ui"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Remembers whether a test failed, so the browser fixture can take a screenshot."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def app_url():
    """Starts the Streamlit app (with fake AI answers) and returns its address."""
    port = free_port()
    env = {**os.environ, "GROQ_API_KEY": "fake-key-for-ui-tests"}
    env.pop("DATACAPILOT_TEST_SCREEN", None)

    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(FAKE_APP),
            "--server.headless", "true",
            "--server.port", str(port),
            "--browser.gatherUsageStats", "false",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 90
    while time.time() < deadline:
        if process.poll() is not None:
            pytest.fail("The Streamlit app stopped while starting")
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as response:
                if response.read().strip() == b"ok":
                    break
        except OSError:
            time.sleep(0.5)
    else:
        process.terminate()
        pytest.fail("The Streamlit app did not become ready within 90 seconds")

    yield url

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture(scope="session")
def browser():
    """One headless Chromium for the whole run. Set HEADED=1 to watch it."""
    sync_api = pytest.importorskip("playwright.sync_api")

    with sync_api.sync_playwright() as playwright:
        chromium = playwright.chromium.launch(headless=os.getenv("HEADED") != "1")
        yield chromium
        chromium.close()


@pytest.fixture
def page(browser, request):
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()
    page.set_default_timeout(45_000)

    yield page

    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        name = "".join(c if c.isalnum() else "_" for c in request.node.name)[:80]
        page.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True)

    context.close()
