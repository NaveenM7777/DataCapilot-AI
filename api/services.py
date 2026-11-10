# Each function wraps one of the existing DataCapilot agents.
# The agents are imported inside the functions (not at the top of the file)
# so the API and its mocked tests can start even when no Groq key is set.


def ask_sql_agent(question: str) -> dict:
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


def ask_excel_agent(question: str) -> dict:
    from excel_agent.code_executor import execute_pandas_code_multi
    from excel_agent.code_generator import generate_pandas_code_multi
    from excel_agent.data_loader import load_all_sheets

    sheets, error = load_all_sheets()
    if error:
        raise ValueError(error)

    code, sheet_var_names = generate_pandas_code_multi(question, sheets)
    result, exec_error = execute_pandas_code_multi(code, sheets, sheet_var_names)

    if exec_error:
        raise ValueError(exec_error.strip())

    return {"code": code, "answer": result.head(20).to_string(index=False)}


def ask_pdf_agent(question: str) -> dict:
    from pdf_agent.pdf_loader import chunk_text, load_default_pdf
    from pdf_agent.qa_generator import generate_answer
    from pdf_agent.retriever import retrieve_relevant_chunks

    _full_text, page_texts, _page_count, error = load_default_pdf()
    if error:
        raise ValueError(error)

    chunks = chunk_text(page_texts)
    relevant = retrieve_relevant_chunks(question, chunks)
    answer = generate_answer(question, relevant)
    pages = sorted({page for chunk in relevant for page in chunk["pages"]})

    return {"answer": answer, "pages": pages}


def ask_ai_agent(question: str) -> dict:
    from ai_agent.orchestrator import run_agent

    result = run_agent(question, [])

    return {"answer": result["answer"], "tools_used": result["tools_used"]}