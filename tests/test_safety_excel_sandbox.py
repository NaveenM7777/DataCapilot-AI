import pandas as pd
import pytest

from excel_agent.code_executor import execute_pandas_code_multi, find_unsafe_code

SHEETS = {
    "Monthly_Sales": pd.DataFrame(
        {"Month": ["Jan", "Feb", "Mar"], "Revenue": [100, 200, 300]}
    ),
    "Store_Locations": pd.DataFrame(
        {
            "City": ["New York", "Toronto", "Chicago"],
            "Country": ["USA", "Canada", "USA"],
            "Monthly_Rent_USD": [6800, 4100, 5900],
        }
    ),
}
NAMES = {
    "Monthly_Sales": "df_monthly_sales",
    "Store_Locations": "df_store_locations",
}


def run(code):
    return execute_pandas_code_multi(code, SHEETS, NAMES)


# Each of these is a way an attacker could steer the AI into writing code that
# breaks out of the sandbox. Every one must be blocked BEFORE it runs.
ATTACKS = {
    "walk-class-hierarchy": "result = len(().__class__.__base__.__subclasses__())",
    "reach-os-via-pandas": "result = pd.__builtins__['__import__']('os').getcwd()",
    "read-file-with-pandas": "result = pd.read_csv('requirements.txt')",
    "read-file-with-numpy": "result = np.loadtxt('requirements.txt', dtype=str)",
    "import-statement": "import os\nresult = 1",
    "format-string-trick": "result = '{0.__class__}'.format(pd)",
    "eval-call": "result = eval('1 + 1')",
    "open-file": "result = open('requirements.txt').read()",
}


@pytest.mark.parametrize("code", ATTACKS.values(), ids=ATTACKS.keys())
def test_sandbox_escape_is_blocked(code):
    result, error = run(code)

    assert result is None
    assert "blocked" in error.lower()


def test_code_cannot_write_files(tmp_path):
    target = tmp_path / "pwned_by_ai.csv"
    code = f"df_monthly_sales.to_csv('{target.as_posix()}')\nresult = 1"

    result, error = run(code)

    assert result is None
    assert not target.exists(), "the attack managed to write a file"


def test_code_cannot_read_files(tmp_path):
    secret_file = tmp_path / "secret.csv"
    secret_file.write_text("password\nTOP-SECRET-123\n")
    code = f"result = pd.read_csv('{secret_file.as_posix()}')"

    result, error = run(code)

    assert result is None
    assert "TOP-SECRET-123" not in error


# The protection must not break normal questions.
NORMAL_QUESTIONS = {
    "sum": ("result = df_monthly_sales['Revenue'].sum()", 600),
    "max-month": (
        "result = df_monthly_sales.loc[df_monthly_sales['Revenue'].idxmax(), 'Month']",
        "Mar",
    ),
    "filter-and-sum": (
        "result = df_store_locations[df_store_locations['Country'] == 'USA']"
        "['Monthly_Rent_USD'].sum()",
        12700,
    ),
    "apply-lambda": (
        "result = df_monthly_sales['Revenue'].apply(lambda x: x * 2).sum()",
        1200,
    ),
    "numpy-round": ("result = np.round(df_monthly_sales['Revenue'].mean(), 1)", 200.0),
    "to-datetime": ("result = pd.to_datetime('2024-01-31').month", 1),
    "string-contains": (
        "result = len(df_store_locations[df_store_locations['City'].str.contains('York')])",
        1,
    ),
}


@pytest.mark.parametrize(
    "code,expected", NORMAL_QUESTIONS.values(), ids=NORMAL_QUESTIONS.keys()
)
def test_normal_questions_still_work(code, expected):
    assert find_unsafe_code(code) is None

    result, error = run(code)

    assert error is None, error
    assert result.iloc[0, 0] == expected