from langchain_core.tools import tool

from sql_agent.sql_generator import generate_sql
from sql_agent.sql_executor import execute_sql

from excel_agent.data_loader import load_all_sheets
from excel_agent.code_generator import generate_pandas_code_multi
from excel_agent.code_executor import execute_pandas_code_multi

from pdf_agent.pdf_loader import load_default_pdf, chunk_text
from pdf_agent.retriever import retrieve_relevant_chunks
from pdf_agent.qa_generator import generate_answer as generate_pdf_answer


@tool
def query_database(question: str) -> str:
    """Query the Chinook SQL database (artists, albums, tracks, customers,
    invoices, employees, etc). Use this for any question about music
    catalog, sales, or customer data stored in the database."""

    try:
        sql_query = generate_sql(question, [])
        result, error = execute_sql(sql_query)

        if error:
            return f"SQL error: {error}"

        preview = result.head(20).to_string(index=False)
        return f"SQL used: {sql_query}\n\nResult:\n{preview}"

    except Exception as e:
        return f"Database tool failed: {str(e)}"


@tool
def query_spreadsheet(question: str) -> str:
    """Query the company spreadsheet, which has multiple sheets: monthly
    sales, store locations, and employee performance. Use this for
    questions about any of that spreadsheet data. This tool automatically
    checks all sheets, not just one."""

    sheets, error = load_all_sheets()

    if error:
        return f"Spreadsheet tool error: {error}"

    try:
        code, sheet_var_names = generate_pandas_code_multi(question, sheets)
        result, exec_error = execute_pandas_code_multi(code, sheets, sheet_var_names)

        if exec_error:
            return f"Spreadsheet tool error: {exec_error}"

        preview = result.head(20).to_string(index=False)
        return f"Pandas code used: {code}\n\nResult:\n{preview}"

    except Exception as e:
        return f"Spreadsheet tool failed: {str(e)}"


@tool
def query_pdf(question: str) -> str:
    """Query the company PDF report — financial highlights, store locations,
    staffing, return policy, data governance, and outlook. Use this for
    questions about that document's content."""

    full_text, page_texts, page_count, error = load_default_pdf()

    if error:
        return f"PDF tool error: {error}"

    try:
        chunks = chunk_text(page_texts)
        relevant_chunks = retrieve_relevant_chunks(question, chunks)
        return generate_pdf_answer(question, relevant_chunks)

    except Exception as e:
        return f"PDF tool failed: {str(e)}"


ALL_TOOLS = [query_database, query_spreadsheet, query_pdf]

TOOL_EXECUTORS = {
    "query_database": query_database,
    "query_spreadsheet": query_spreadsheet,
    "query_pdf": query_pdf,
}