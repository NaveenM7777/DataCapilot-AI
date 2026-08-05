from database.db_connection import get_schema
from llm.groq_client import ask_groq


def generate_sql(user_question, chat_history=None):
    """
    Converts a natural language question
    into a SQL query using the LLM.
    """

    schema = get_schema()

    conversation = ""

    if chat_history and len(chat_history) > 0:

        last_chat = chat_history[-1]

        conversation = f"""
Previous User Question:
{last_chat['question']}

Previous SQL Query:
{last_chat['sql']}
"""

    prompt = f"""
You are an expert SQLite SQL developer.

Your task is to convert natural language into valid SQLite SQL.

Database Schema:
{schema}

Previous Conversation:
{conversation}

Current User Question:
{user_question}

Rules:

1. Generate ONLY a valid SQLite SQL query.
2. Do NOT include explanations.
3. Do NOT use markdown.
4. Use ONLY the tables and columns provided.
5. Return ONLY one SQL query.
6. Generate only SELECT statements.
7. Never generate:
   - INSERT
   - UPDATE
   - DELETE
   - DROP
   - ALTER
   - CREATE
8. If the user asks a follow-up question like:
   "Only from Brazil"
   "Sort by Name"
   "Only top 5"
   use the previous conversation to understand the context.
9. Prefer LIMIT 10 if the user asks for "top" records.
10. Output ONLY SQL.

SQL:
"""

    sql_query = ask_groq(prompt)

    sql_query = _clean_sql(sql_query)

    return sql_query


def _clean_sql(raw_sql):
    """
    Removes markdown code fences or stray labels.
    """

    cleaned = raw_sql.strip()

    if cleaned.startswith("```"):

        cleaned = cleaned.strip("`")

        if cleaned.lower().startswith("sql"):

            cleaned = cleaned[3:]

    return cleaned.strip()