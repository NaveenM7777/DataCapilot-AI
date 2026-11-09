import pytest

# golden file / test "agent" name -> function in api/services.py
SERVICE_FUNCTIONS = {
    "sql": "ask_sql_agent",
    "excel": "ask_excel_agent",
    "pdf": "ask_pdf_agent",
    "orchestrator": "ask_ai_agent",
}

# Your tools catch every exception and return it as plain text such as
# "Database tool failed: Connection error." These words tell us the problem
# was the network or the Groq quota, not a wrong answer.
ENVIRONMENT_ERROR_HINTS = [
    "connection error",
    "getaddrinfo",
    "timed out",
    "timeout",
    "rate limit",
    "429",
]


def skip_if_tool_failed(result):
    """Skips for network problems, fails clearly for any other tool crash."""
    text = result["answer"].lower()
    if "tool failed" not in text:
        return
    if any(hint in text for hint in ENVIRONMENT_ERROR_HINTS):
        pytest.skip(
            "Environment problem, not an agent bug: a tool could not reach Groq "
            "(check your internet connection or rate limit, then re-run)"
        )
    pytest.fail("A tool crashed instead of answering:\n" + result["answer"])


def ask(agent, question):
    import groq

    from api import services

    function = getattr(services, SERVICE_FUNCTIONS[agent])
    try:
        return function(question)
    except (groq.APIConnectionError, groq.RateLimitError) as exc:
        # A network or quota problem says nothing about answer quality,
        # so report it as "skipped" instead of "agent is wrong".
        pytest.skip(
            f"Environment problem, not an agent bug: {type(exc).__name__} "
            "(check your internet connection or Groq rate limit, then re-run)"
        )