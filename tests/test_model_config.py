import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The app's own code. (tests/ and evals/ are not scanned: the AI judge
# deliberately uses a different model.)
APP_FOLDERS = ["ai_agent", "excel_agent", "pdf_agent", "sql_agent", "llm", "ui", "api", "database"]


def app_python_files():
    yield ROOT / "app.py"
    for folder in APP_FOLDERS:
        yield from (ROOT / folder).rglob("*.py")


def test_the_model_name_is_defined_in_one_place():
    config = ROOT / "llm" / "config.py"
    offenders = []

    for path in app_python_files():
        if path == config or not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            if re.search(r"""model\s*=\s*["']""", line) or re.search(r"gpt-oss-\d+b", line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")

    assert not offenders, (
        "A model name is typed directly into the code. Use MODEL from llm/config.py:\n"
        + "\n".join(offenders)
    )
