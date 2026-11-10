import ast
import pandas as pd
import numpy as np


BLOCKED_PATTERNS = [".plot(", ".hist(", "matplotlib", "pyplot", ".show("]

# --- Safety rules for AI-written code ---------------------------------------
# The AI writes pandas code and we run it with exec(). Restricting __builtins__
# is not enough, because `pd` and `np` give the code a way out (for example
# pd.__builtins__ reaches the os module, and pd.read_csv can read any file).
# So the code is checked BEFORE it runs.

DENIED_NAMES = {
    "eval", "exec", "compile", "open", "getattr", "setattr", "delattr",
    "globals", "locals", "vars", "input", "breakpoint", "exit", "quit",
    "os", "sys", "subprocess", "importlib", "builtins",
}

DENIED_ATTRIBUTES = {
    "eval", "exec", "compile", "open", "system", "popen",
    # numpy file access
    "load", "loads", "loadtxt", "genfromtxt", "fromfile", "tofile", "save",
    "savetxt", "savez", "savez_compressed", "memmap",
    # pandas file writing
    "to_csv", "to_excel", "to_json", "to_pickle", "to_sql", "to_parquet",
    "to_feather", "to_hdf", "to_xml", "to_clipboard", "to_latex", "to_html",
    "to_markdown", "to_stata", "to_orc",
}


def find_unsafe_code(code):
    """
    Returns a short reason if the code does something we do not allow,
    or None if it looks safe. (This lowers the risk but is not a full sandbox.
    A real sandbox runs the code in a separate, locked-down process.)
    """

    tree = ast.parse(code)

    for node in ast.walk(tree):

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "import statements are not allowed"

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                return f"access to '{node.attr}' is not allowed"
            if node.attr in DENIED_ATTRIBUTES or node.attr.startswith("read_"):
                return f"'{node.attr}' is not allowed (file access)"

        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in DENIED_NAMES:
                return f"'{node.id}' is not allowed"

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "__" in node.value:
                return "text containing '__' is not allowed"

    return None


def _blocked_message(reason):
    return (
        f"🔒 The generated code was blocked for safety: {reason}.\n\n"
        "Try rephrasing your question to ask for a calculation on the data."
    )


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

    unsafe_reason = find_unsafe_code(code)

    if unsafe_reason:
        return None, _blocked_message(unsafe_reason)

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

    unsafe_reason = find_unsafe_code(code)

    if unsafe_reason:
        return None, _blocked_message(unsafe_reason)

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