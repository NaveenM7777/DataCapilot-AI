import pytest

from sql_agent.sql_executor import validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT COUNT(*) FROM Customer",
        "SELECT Name FROM Artist LIMIT 5",
        "SELECT * FROM Track WHERE Name LIKE '%love%'",
    ],
)
def test_validator_allows_normal_selects(sql):
    is_valid, error = validate_sql(sql)
    assert is_valid is True, error


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE Customer",
        "DELETE FROM Customer",
        "UPDATE Customer SET Country = 'X'",
        "INSERT INTO Artist (Name) VALUES ('x')",
        "SELECT 1; DROP TABLE Customer",
        "ALTER TABLE Customer ADD COLUMN x TEXT",
    ],
)
def test_validator_blocks_dangerous_sql(sql):
    is_valid, _ = validate_sql(sql)
    assert is_valid is False


def test_validator_allows_alternative_genre():
    """'Alternative' contains the letters ALTER, but it is just a genre name."""
    sql = (
        "SELECT COUNT(*) FROM Track t JOIN Genre g ON t.GenreId = g.GenreId "
        "WHERE g.Name = 'Alternative'"
    )
    is_valid, error = validate_sql(sql)
    assert is_valid is True, error


def test_validator_ignores_keywords_inside_quotes():
    is_valid, error = validate_sql("SELECT * FROM Artist WHERE Name = 'Drop Dead'")
    assert is_valid is True, error


def test_validator_blocks_multiple_statements():
    is_valid, _ = validate_sql("SELECT 1; SELECT 2")
    assert is_valid is False