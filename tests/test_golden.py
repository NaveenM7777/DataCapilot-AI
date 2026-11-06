import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from answer_matching import contains_expected, normalize

load_dotenv()

pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY is not set"),
]

GOLDEN_FILE = Path(__file__).parent / "data" / "golden_questions.json"
GOLDEN = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))

# golden file "agent" name -> function in api/services.py
SERVICE_FUNCTIONS = {
    "sql": "ask_sql_agent",
    "excel": "ask_excel_agent",
    "pdf": "ask_pdf_agent",
    "orchestrator": "ask_ai_agent",
}

NOT_FOUND_PHRASES = [
    "couldn't find",
    "couldn\u2019t find",
    "could not find",
    "cannot find",
    "can't find",
    "not mentioned",
    "not provided",
    "not specified",
    "not stated",
    "no information",
    "doesn't mention",
    "does not mention",
]


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


def details(case, result):
    lines = [
        f"Agent   : {case['agent']}",
        f"Question: {case['question']}",
        f"Expected: {case['expected']}",
    ]
    for key in ("sql", "code", "pages", "tools_used"):
        if key in result:
            lines.append(f"{key:<8}: {result[key]}")
    lines.append(f"Answer  : {result['answer']}")
    lines.append(f"Raw     : {ascii(result['answer'])}")  # makes invisible characters visible
    return "\n" + "\n".join(lines)


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_agent_gives_correct_answer(case):
    result = ask(case["agent"], case["question"])
    skip_if_tool_failed(result)

    expected = case["expected"]
    expected_values = expected if isinstance(expected, list) else [expected]
    missing = [v for v in expected_values if not contains_expected(v, result["answer"])]

    assert not missing, f"Wrong answer. Missing: {missing}" + details(case, result)

    if "expected_tools" in case:
        used = set(result["tools_used"])
        wanted = set(case["expected_tools"])
        assert wanted <= used, (
            f"Wrong routing. Wanted tools {sorted(wanted)}, used {sorted(used)}"
            + details(case, result)
        )


def test_pdf_agent_admits_when_answer_is_missing():
    """The PDF has no CEO. A good agent says so instead of inventing a name."""
    result = ask("pdf", "Who is the CEO of Chinook Music Retail?")

    answer = normalize(result["answer"]).lower()
    assert any(phrase in answer for phrase in NOT_FOUND_PHRASES), (
        "The agent should say the information is not in the document.\n"
        f"Answer: {result['answer']}"
    )