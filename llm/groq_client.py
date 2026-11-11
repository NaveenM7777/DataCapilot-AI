from groq import Groq
from dotenv import load_dotenv
from llm.config import MODEL
import os

# Load environment variables
load_dotenv()

# Create Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def ask_groq(prompt):
    """
    Sends a prompt to the Groq LLM
    and returns the generated response.
    """

    response = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0

    )

    return response.choices[0].message.content


def explain_sql(sql_query):
    """
    Explains the generated SQL query
    in simple English.
    """

    prompt = f"""
You are an expert SQL teacher.

Explain the following SQLite SQL query in simple, beginner-friendly English.

Rules:
1. Do not explain SQL syntax.
2. Explain only what the query does.
3. Keep the explanation within 2-3 sentences.
4. Do not mention databases unless necessary.
5. Make the explanation easy for beginners.

SQL Query:
{sql_query}
"""

    response = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0

    )

    return response.choices[0].message.content