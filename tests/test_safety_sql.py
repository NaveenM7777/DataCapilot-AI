import sqlite3
from pathlib import Path

import pytest

from sql_agent.sql_executor import execute_sql, validate_sql

DB_FILE = Path(__file__).resolve().parent.parent / "database" / "chinook.db"

pytestmark = pytest.mark.skipif(not DB_FILE.exists(), reason="sample database is missing")

ATTACKS = {
    "stacked-drop": "SELECT 1; DROP TABLE Customer",
    "lowercase-drop": "select 1; drop table customer",
    "comment-hides-drop": "SELECT 1 /* x */; DROP TABLE Customer",
    "newline-drop": "SELECT 1\n;\nDROP TABLE Customer",
    "cte-delete": "WITH x AS (SELECT 1) DELETE FROM Customer",
    "attach-database": "SELECT 1; ATTACH DATABASE 'x.db' AS x",
    "leading-spaces-drop": "   DROP TABLE Customer",
    "update-in-select": "SELECT 1; UPDATE Customer SET Country = 'X'",
}


def customer_count():
    conn = sqlite3.connect(DB_FILE)
    try:
        return conn.execute("SELECT COUNT(*) FROM Customer").fetchone()[0]
    finally:
        conn.close()


@pytest.mark.parametrize("sql", ATTACKS.values(), ids=ATTACKS.keys())
def test_destructive_sql_is_rejected(sql):
    is_valid, _ = validate_sql(sql)
    assert is_valid is False


def test_database_is_unchanged_after_all_attacks():
    before = customer_count()

    for sql in ATTACKS.values():
        result, error = execute_sql(sql)
        assert result is None
        assert error is not None

    assert customer_count() == before


def test_load_extension_cannot_run():
    """The validator lets this through, but SQLite itself refuses it."""
    result, error = execute_sql("SELECT load_extension('evil')")

    assert result is None
    assert "not authorized" in error


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN GAP: customer emails and phone numbers can be queried freely. "
        "There is no column-level protection for personal data."
    ),
)
def test_personal_data_columns_are_protected():
    result, error = execute_sql("SELECT Email, Phone FROM Customer LIMIT 3")

    assert result is None, "personal data was returned without restriction"