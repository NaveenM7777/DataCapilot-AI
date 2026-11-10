"""
Spike: can DeepEval use a Groq model as its judge?
Run once to check the setup, before building real evaluation tests.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deepeval.metrics import FaithfulnessMetric  # noqa: E402
from deepeval.test_case import LLMTestCase  # noqa: E402

from evals.groq_judge import GroqJudge  # noqa: E402

CONTEXT = [
    "Customers may return physical media within 30 days of purchase. "
    "Refunds are processed in 5 to 7 business days."
]

CASES = [
    ("faithful answer", "You can return physical media within 30 days.", True),
    ("made-up answer", "You can return physical media within 90 days, and refunds are instant.", False),
]


def main():
    judge = GroqJudge()
    print(f"Judge model: {judge.get_model_name()}\n")

    for name, answer, should_pass in CASES:
        metric = FaithfulnessMetric(model=judge, threshold=0.7, include_reason=True)
        test_case = LLMTestCase(
            input="What is the return window for physical media?",
            actual_output=answer,
            retrieval_context=CONTEXT,
        )
        metric.measure(test_case)
        verdict = "PASS" if metric.is_successful() else "FAIL"
        expected = "PASS" if should_pass else "FAIL"
        print(f"{name}: score={metric.score:.2f} -> {verdict} (we expected {expected})")
        print(f"  reason: {metric.reason}\n")


if __name__ == "__main__":
    main()