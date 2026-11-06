import re

from database.db_connection import run_query


BLOCKED_COMMANDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
]


def _remove_string_literals(sql):
    """
    Replaces 'quoted text' with an empty string so that words inside
    quotes (for example the genre 'Alternative') are not mistaken
    for SQL commands.
    """

    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def validate_sql(sql_query):
    """
    Allows only safe SELECT queries.
    Blocks dangerous SQL commands.
    """

    sql = sql_query.strip()

    # Allow only SELECT queries
    if not sql.upper().startswith("SELECT"):
        return False, "❌ Only SELECT queries are allowed."

    # Look only at the SQL itself, not at text inside quotes
    checkable = _remove_string_literals(sql).upper()

    # Block more than one statement
    if ";" in checkable.rstrip().rstrip(";"):
        return False, "❌ Multiple statements are not allowed."

    # Block dangerous commands (whole words only)
    for command in BLOCKED_COMMANDS:
        if re.search(rf"\b{command}\b", checkable):
            return False, f"❌ '{command}' queries are not allowed."

    return True, None


def execute_sql(sql_query):
    """
    Validates and executes the SQL query.
    Returns the result DataFrame or an error.
    """

    # -----------------------------
    # SQL Validation
    # -----------------------------
    is_valid, validation_error = validate_sql(sql_query)

    if not is_valid:
        return None, validation_error

    # -----------------------------
    # Execute SQL
    # -----------------------------
    try:

        result = run_query(sql_query)

        return result, None

    except Exception as e:

        error_message = f"""
❌ Unable to execute the generated SQL.

Possible Reasons:
• The AI generated an invalid SQL query.
• Table or column may not exist.
• SQLite does not support the generated syntax.

Technical Error:
{str(e)}
"""

        return None, error_message