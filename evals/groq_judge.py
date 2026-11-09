import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from deepeval.models import DeepEvalBaseLLM

load_dotenv()

# A DIFFERENT model family from the one the app uses (openai/gpt-oss-120b), so
# the judge is not grading its own homework. Override it in .env with
# GROQ_JUDGE_MODEL=... if Groq changes the available models.
DEFAULT_JUDGE_MODEL = "qwen/qwen3.8-27b"


def extract_json(text):
    """
    Keeps only the JSON object from a model reply.
    Some models print their reasoning first (<think>...</think>) or wrap the
    JSON in ``` fences or extra words.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"The judge did not return JSON: {text[:200]}")
    return text[start : end + 1]


class GroqJudge(DeepEvalBaseLLM):
    """Lets DeepEval use a Groq model as the 'judge' that scores answers."""

    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("GROQ_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
        super().__init__(self.model_name)

    def load_model(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
        return Groq(api_key=api_key)

    def _chat(self, messages, json_mode):
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        response = self.model.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0,
            **extra,
        )
        return response.choices[0].message.content or ""

    def generate(self, prompt, schema=None):
        if schema is None:
            return self._chat([{"role": "user", "content": prompt}], json_mode=False)

        hint = (
            "\n\nReturn ONLY a valid JSON object that follows this JSON schema, "
            "with no other text:\n" + json.dumps(schema.model_json_schema())
        )
        messages = [{"role": "user", "content": prompt + hint}]

        try:
            text = self._chat(messages, json_mode=True)
        except Exception:
            # Some models do not support JSON mode. The prompt already asks
            # for JSON, so try again without it.
            text = self._chat(messages, json_mode=False)

        return schema.model_validate(json.loads(extract_json(text)))

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema)

    def get_model_name(self):
        return self.model_name
