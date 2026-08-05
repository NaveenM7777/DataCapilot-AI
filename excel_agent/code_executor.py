import ast
import pandas as pd
import numpy as np


BLOCKED_PATTERNS = [".plot(", ".hist(", "matplotlib", "pyplot", ".show("]


def execute_pandas_code(code, df):
    """
    Single-sheet version — used by the Excel Agent TAB.
    """

    if any(pattern in code for pattern in BLOCKED_PATTERNS):
        return None, (
            "The generated code tried to create a plot/chart directly, which "
            "isn't supported here — charts are shown automatically for "
            "numeric results. Try rephrasing to ask for a summary or specific "
            "numbers instead (e.g. 'show me revenue by month' instead of "
            "'plot revenue by month')."
        )

    try:
        ast.parse(code)
    except SyntaxError as e:
        return None, (
            f"The generated code had invalid syntax: {e.msg} (line {e.lineno}).\n\n"
            f"Raw generated code was:\n{code}\n\n"
            "Try rephrasing your question."
        )

    safe_globals = {
        "__builtins__": {
            "len": len,
            "range": range,
            "sum": sum,
            "min": min,
            "max": max,
            "sorted": sorted,
            "round": round,
            "abs": abs,
        },
        "pd": pd,
        "np": np,
    }

    safe_locals = {"df": df.copy()}

    try:
        exec(code, safe_globals, safe_locals)

        if "result" not in safe_locals:
            return None, "The generated code did not produce a `result` variable."

        result = safe_locals["result"]

        if isinstance(result, pd.Series):
            result = result.reset_index()

        elif not isinstance(result, pd.DataFrame):
            result = pd.DataFrame({"result": [result]})

        return result, None

    except Exception as e:
        return None, f"Error running generated code: {str(e)}"


def execute_pandas_code_multi(code, sheets, sheet_var_names):
    """
    Multi-sheet version — used by the AI AGENT. Makes ALL sheets available
    as separate variables (df_monthly_sales, df_store_locations, etc.)
    instead of just one `df`.
    """

    if any(pattern in code for pattern in BLOCKED_PATTERNS):
        return None, (
            "The generated code tried to create a plot/chart directly, which "
            "isn't supported here. Try rephrasing to ask for a summary or "
            "specific numbers instead."
        )

    try:
        ast.parse(code)
    except SyntaxError as e:
        return None, (
            f"The generated code had invalid syntax: {e.msg} (line {e.lineno}).\n\n"
            f"Raw generated code was:\n{code}\n\n"
            "Try rephrasing your question."
        )

    safe_globals = {
        "__builtins__": {
            "len": len,
            "range": range,
            "sum": sum,
            "min": min,
            "max": max,
            "sorted": sorted,
            "round": round,
            "abs": abs,
        },
        "pd": pd,
        "np": np,
    }

    safe_locals = {
        sheet_var_names[name]: df.copy() for name, df in sheets.items()
    }

    try:
        exec(code, safe_globals, safe_locals)

        if "result" not in safe_locals:
            return None, "The generated code did not produce a `result` variable."

        result = safe_locals["result"]

        if isinstance(result, pd.Series):
            result = result.to_frame()

        elif not isinstance(result, pd.DataFrame):
            result = pd.DataFrame({"result": [result]})

        return result, None

    except Exception as e:
        return None, f"Error running generated code: {str(e)}"