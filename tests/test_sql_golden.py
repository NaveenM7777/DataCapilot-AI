import json
import os
import re
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY is not set"),
]

GOLDEN_FILE = Path(__file__).parent / "data" / "golden_questions.json"
GOLDEN = json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))


def numbers_in(text):
    return re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_sql_agent_gives_correct_answer(case):
    from api.services import ask_sql_agent

    result = ask_sql_agent(case["question"])

    assert case["expected"] in numbers_in(result["answer"]), (
        f"\nQuestion: {case['question']}"
        f"\nExpected: {case['expected']}"
        f"\nSQL used: {result['sql']}"
        f"\nAnswer  : {result['answer']}"
    )