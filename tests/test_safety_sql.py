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


PERSONAL_DATA_QUERIES = {
    "email-column": "SELECT Email FROM Customer",
    "email-and-phone": "SELECT Email, Phone FROM Customer LIMIT 3",
    "lowercase": "select email from customer",
    "employee-fax": "SELECT Fax FROM Employee",
    "address": "SELECT Address FROM Customer",
    "select-star": "SELECT * FROM Customer",
    "alias-star": "SELECT c.* FROM Customer c",
    "billing-address": "SELECT BillingAddress FROM Invoice",
}


@pytest.mark.parametrize("sql", PERSONAL_DATA_QUERIES.values(), ids=PERSONAL_DATA_QUERIES.keys())
def test_personal_data_is_blocked(sql):
    result, error = execute_sql(sql)

    assert result is None, "personal data was returned without restriction"
    assert "personal data" in error.lower()


# The protection must not break normal questions.
NORMAL_QUERIES = {
    "count-star": "SELECT COUNT(*) FROM Customer",
    "group-by-country": "SELECT Country, COUNT(*) AS customers FROM Customer GROUP BY Country",
    "multiplication": "SELECT SUM(UnitPrice * Quantity) FROM InvoiceLine",
    "select-star-from-track": "SELECT * FROM Track LIMIT 3",
    "names-only": "SELECT FirstName, LastName FROM Customer LIMIT 3",
}


@pytest.mark.parametrize("sql", NORMAL_QUERIES.values(), ids=NORMAL_QUERIES.keys())
def test_normal_queries_still_work(sql):
    result, error = execute_sql(sql)

    assert error is None, error
    assert result is not None and not result.empty
