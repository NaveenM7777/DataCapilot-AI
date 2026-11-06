def ask_sql_agent(question: str) -> dict:
    # Imported here, not at the top of the file, so the API and its mocked
    # tests can start even when no Groq key is set (for example in CI).
    from sql_agent.sql_executor import execute_sql
    from sql_agent.sql_generator import generate_sql

    sql = generate_sql(question, [])
    result, error = execute_sql(sql)

    if error:
        raise ValueError(f"SQL could not run: {error.strip()}")

    if result.empty:
        answer = "No matching data was found."
    else:
        answer = result.head(20).to_string(index=False)

    return {"sql": sql, "answer": answer}


def ask_excel_agent(content: bytes, filename: str, question: str) -> dict:
    """Placeholder. Next we connect your real Excel agent."""
    return {"answer": f"(stub) {filename} has {len(content)} bytes. Q: {question}"}


def ask_pdf_agent(content: bytes, filename: str, question: str) -> dict:
    """Placeholder. Next we connect your real PDF agent."""
    return {"answer": f"(stub) {filename} has {len(content)} bytes. Q: {question}"}