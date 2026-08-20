import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _extract_code(raw_text):

    fenced = re.search(r"```(?:python)?\s*(.*?)```", raw_text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()

    lines = raw_text.strip().split("\n")

    code_lines = [
        line for line in lines
        if not re.match(r"^(here|this|the code|sure|okay)\b", line.strip(), re.IGNORECASE)
    ]

    return "\n".join(code_lines).strip()


def generate_pandas_code(question, df, chat_history=None):
    """
    Single-sheet version — used by the Excel Agent TAB, where one
    specific sheet is currently selected.
    """

    columns_info = ", ".join(f"{col} ({df[col].dtype})" for col in df.columns)
    sample_rows = df.head(3).to_string(index=False)

    history_text = ""

    if chat_history:
        recent = chat_history[-3:]
        for chat in recent:
            history_text += f"Q: {chat['question']}\nCode: {chat['code']}\n\n"

    system_prompt = (
        "You are a pandas expert. Given a DataFrame called `df` with the "
        "following columns, dtypes, and sample rows, write ONLY a short "
        "pandas code snippet that computes the answer to the user's question "
        "and assigns the final answer to a variable named `result`. "
        "IMPORTANT: match text values using the exact format shown in the "
        "sample rows (e.g. if months are stored as 'Dec', do not filter for "
        "'December' — use .str.contains(..., case=False) for partial/flexible "
        "matching when unsure of exact formatting, instead of exact equality. "
        "Do not import anything. Do not read or write files. Do not use exec/eval. "
        "NEVER call .plot(), .hist(), or any matplotlib/visualization method — "
        "charts are handled separately by the app. If asked to 'analyze' or "
        "give 'insights', just compute relevant summary statistics (e.g. "
        "describe(), groupby, sum, mean) and assign that to `result` — do not "
        "attempt to generate a plot or image. "
        "Write the code as a single line if possible. Use double quotes for "
        "strings, never single quotes, to avoid conflicts with apostrophes. "
        "Respond with ONLY the raw code and nothing else — no explanation "
        "before or after it, no markdown fences, no backticks, no comments."
    )

    user_prompt = (
        f"DataFrame columns: {columns_info}\n\n"
        f"Sample rows:\n{sample_rows}\n\n"
        f"Previous questions in this session:\n{history_text}\n"
        f"Question: {question}\n\n"
        "pandas code:"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    return _extract_code(raw)


def generate_pandas_code_multi(question, sheets, chat_history=None):
    """
    Multi-sheet version — used by the AI AGENT, which needs to see
    every sheet (Monthly_Sales, Store_Locations, Employee_Performance)
    at once, since it doesn't know in advance which one has the answer.
    Each sheet becomes a variable named df_<sheet_name>.
    """

    sheet_var_names = {}
    schema_parts = []

    for sheet_name, df in sheets.items():

        var_name = "df_" + re.sub(r"[^a-zA-Z0-9_]", "_", sheet_name.lower())
        sheet_var_names[sheet_name] = var_name

        columns_info = ", ".join(f"{col} ({df[col].dtype})" for col in df.columns)
        sample_rows = df.head(3).to_string(index=False)

        schema_parts.append(
            f"Variable `{var_name}` (sheet: {sheet_name}):\n"
            f"Columns: {columns_info}\n"
            f"Sample rows:\n{sample_rows}\n"
        )

    schema_text = "\n".join(schema_parts)

    history_text = ""

    if chat_history:
        recent = chat_history[-3:]
        for chat in recent:
            history_text += f"Q: {chat['question']}\nCode: {chat['code']}\n\n"

    system_prompt = (
        "You are a pandas expert. You have access to multiple DataFrames, "
        "one per spreadsheet sheet, given below as separate variables. "
        "Write ONLY a short pandas code snippet that computes the answer to "
        "the user's question and assigns the final answer to a variable "
        "named `result`. Use whichever variable(s) are relevant to the "
        "question — check ALL of them if unsure which sheet has the answer. "
        "If a question needs data from multiple sheets, combine them "
        "(e.g. merge, concat) as needed. "
        "Match text values using the exact format shown in the sample rows "
        "(e.g. if months are stored as 'Dec', don't filter for 'December' — "
        "use .str.contains(case=False) for flexible matching if unsure). "
        "Do not import anything. Do not read or write files. Do not use exec/eval. "
        "NEVER call .plot(), .hist(), or any matplotlib/visualization method — "
        "charts are handled separately by the app. If asked to 'analyze' or "
        "give 'insights', just compute relevant summary statistics and assign "
        "that to `result` — do not attempt to generate a plot or image. "
        "Use double quotes for strings, never single quotes. "
        "Respond with ONLY the raw code and nothing else — no explanation, "
        "no markdown fences, no backticks, no comments."
    )

    user_prompt = (
        f"Available DataFrames:\n{schema_text}\n\n"
        f"Previous questions in this session:\n{history_text}\n"
        f"Question: {question}\n\n"
        "pandas code:"
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    return _extract_code(raw), sheet_var_names


def explain_pandas_code(code):

    system_prompt = (
        "Explain the following pandas code in 1-3 simple sentences, "
        "for a non-technical user. Do not repeat the code itself."
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": code}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()