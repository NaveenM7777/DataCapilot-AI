"""
Answer-QUALITY tests for the PDF agent, scored by DeepEval with a Groq judge.

Golden tests check that an answer contains the right fact. These tests ask a
different question: is the answer actually SUPPORTED by the text the agent
retrieved (faithfulness), and does it address what was asked (relevancy)?

Run these in the evaluation environment:  venv-eval
In the normal environment (and CI) this whole file is skipped.
"""
import json
import os
import re
from pathlib import Path

import pytest
from dotenv import load_dotenv

pytest.importorskip("deepeval", reason="DeepEval is not installed (use the venv-eval environment)")

from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric  # noqa: E402
from deepeval.test_case import LLMTestCase  # noqa: E402

load_dotenv()
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

pytestmark = [
    pytest.mark.llm,
    pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY is not set"),
]

THRESHOLD = 0.7
# Relevancy is deliberately more forgiving than faithfulness. DeepEval splits an
# answer into statements and judges each one, so in a one-sentence answer a single
# helpful extra detail (a store ID) can cost a third of the score. Faithfulness
# (no hallucination) stays strict.
RELEVANCY_THRESHOLD = 0.6
REPORT_DIR = Path(__file__).resolve().parent.parent / "reports" / "llm" / "deepeval_pdf"

QUESTIONS = [
    "What is the return window for physical media?",
    "Where is the planned sixth store location?",
    "What is the total annual revenue reported?",
    "Which store is the oldest?",
    "How many business days does it take to process refunds?",
]


@pytest.fixture(scope="module")
def judge():
    from evals.groq_judge import GroqJudge

    return GroqJudge()


def measure_or_skip(metric, test_case):
    """Scores a test case. Network and rate-limit problems are skipped, not failed."""
    try:
        metric.measure(test_case)
    except Exception as exc:
        text = f"{type(exc).__name__} {exc}".lower()
        if any(hint in text for hint in ("connection", "rate limit", "429", "timed out", "getaddrinfo")):
            pytest.skip(f"Environment problem, not a quality problem: {type(exc).__name__}")
        raise


def score_with_confirmation(make_metric, test_case):
    """
    LLM judges are noisy: the SAME answer once scored 0.33 ("the document says
    Toronto is the oldest store" - it does not) and 1.0 on the next run.
    So a failing metric is scored a second time, and only a second failure counts.
    Returns (final_metric, first_failed_metric_or_None).
    """
    first = make_metric()
    measure_or_skip(first, test_case)
    if first.is_successful():
        return first, None

    second = make_metric()
    measure_or_skip(second, test_case)
    return second, first


def save_scores(question, answer, results):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", question.lower()).strip("_")[:60]
    (REPORT_DIR / f"{slug}.json").write_text(json.dumps({"question": question, "answer": answer, **results}, indent=2))


def run_pdf_agent(question):
    """Runs the real PDF agent and also returns the text chunks it retrieved."""
    import groq

    from pdf_agent.pdf_loader import chunk_text, load_default_pdf
    from pdf_agent.qa_generator import generate_answer
    from pdf_agent.retriever import retrieve_relevant_chunks

    _text, page_texts, _count, error = load_default_pdf()
    assert error is None, error

    chunks = retrieve_relevant_chunks(question, chunk_text(page_texts))
    try:
        answer = generate_answer(question, chunks)
    except (groq.APIConnectionError, groq.RateLimitError) as exc:
        pytest.skip(f"Environment problem, not a quality problem: {type(exc).__name__}")

    return answer, [chunk["text"] for chunk in chunks]


# --- 1. Is the judge itself trustworthy? -------------------------------------
# Before trusting scores, check that the judge can tell a good answer from a
# made-up one. If this fails, every other score in this file means nothing.

JUDGE_CONTEXT = [
    "Customers may return physical media within 30 days of purchase. "
    "Refunds are processed in 5 to 7 business days."
]


def test_judge_accepts_a_faithful_answer(judge):
    metric = FaithfulnessMetric(model=judge, threshold=THRESHOLD, include_reason=True, async_mode=False)
    case = LLMTestCase(
        input="What is the return window?",
        actual_output="Physical media can be returned within 30 days.",
        retrieval_context=JUDGE_CONTEXT,
    )
    measure_or_skip(metric, case)

    assert metric.is_successful(), f"score {metric.score}: {metric.reason}"


def test_judge_rejects_a_made_up_answer(judge):
    metric = FaithfulnessMetric(model=judge, threshold=THRESHOLD, include_reason=True, async_mode=False)
    case = LLMTestCase(
        input="What is the return window?",
        actual_output="Physical media can be returned within 90 days and refunds are instant.",
        retrieval_context=JUDGE_CONTEXT,
    )
    measure_or_skip(metric, case)

    assert not metric.is_successful(), (
        f"The judge accepted an answer that contradicts the document (score {metric.score})"
    )


# --- 2. Real quality scores for the PDF agent --------------------------------


@pytest.mark.parametrize("question", QUESTIONS)
def test_pdf_answer_is_faithful_and_relevant(judge, question):
    answer, context = run_pdf_agent(question)

    test_case = LLMTestCase(input=question, actual_output=answer, retrieval_context=context)

    def new_faithfulness():
        return FaithfulnessMetric(model=judge, threshold=THRESHOLD, include_reason=True, async_mode=False)

    def new_relevancy():
        return AnswerRelevancyMetric(model=judge, threshold=RELEVANCY_THRESHOLD, include_reason=True, async_mode=False)

    faithfulness, faithfulness_first = score_with_confirmation(new_faithfulness, test_case)
    relevancy, relevancy_first = score_with_confirmation(new_relevancy, test_case)

    save_scores(
        question,
        answer,
        {
            "faithfulness": faithfulness.score,
            "faithfulness_first_try": faithfulness_first.score if faithfulness_first else None,
            "answer_relevancy": relevancy.score,
            "answer_relevancy_first_try": relevancy_first.score if relevancy_first else None,
        },
    )

    problems = []
    if not faithfulness.is_successful():
        problems.append(
            f"NOT FAITHFUL twice (scores {faithfulness_first.score} then {faithfulness.score}): "
            f"{faithfulness.reason}"
        )
    if not relevancy.is_successful():
        problems.append(
            f"NOT RELEVANT twice (scores {relevancy_first.score} then {relevancy.score}): "
            f"{relevancy.reason}"
        )

    assert not problems, f"\nQuestion: {question}\nAnswer  : {answer}\n" + "\n".join(problems)
