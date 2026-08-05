from database.db_connection import run_query


def validate_sql(sql_query):
    """
    Allows only safe SELECT queries.
    Blocks dangerous SQL commands.
    """

    sql = sql_query.strip().upper()

    blocked_commands = [
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
        "PRAGMA"
    ]

    # Allow only SELECT queries
    if not sql.startswith("SELECT"):
        return False, "❌ Only SELECT queries are allowed."

    # Block dangerous commands
    for command in blocked_commands:
        if command in sql:
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