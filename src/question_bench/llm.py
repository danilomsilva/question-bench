"""Question generation.

``QuestionGenerator`` is the seam for the LLM. The real Gemini client will
implement the same call; ``StubQuestionGenerator`` fabricates deterministic,
rule-passing questions so the rest of the system can be built and tested
without a network or an API key.
"""

from __future__ import annotations
import json
from typing import Any, Protocol
from pydantic import ValidationError
from question_bench.models import (
    MultipleChoiceQuestion,
    Question,
    QuestionAdapter,
    ShortAnswerQuestion,
)


class GenerationError(RuntimeError):
    """Raised when the underlying generator fails (network, quota, bad output)."""


class QuestionGenerator(Protocol):
    def generate(
        self, *, question_type: str, skill_tag: str, count: int, prompt_version: str
    ) -> list[Question]: ...


class StubQuestionGenerator:
    """Deterministic fake generator. No LLM, no randomness."""

    def generate(
        self, *, question_type: str, skill_tag: str, count: int, prompt_version: str
    ) -> list[Question]:
        if question_type == "multiple_choice":
            return [
                MultipleChoiceQuestion(
                    stem=f"Sample multiple-choice question about {skill_tag} (#{i})",
                    skill_tag=skill_tag,
                    prompt_version=prompt_version,
                    # All options length 5 so the distractor-length rule passes.
                    options=["alpha", "bravo", "delta", "gamma"],
                    correct_answer="alpha",
                )
                for i in range(count)
            ]
        return [
            ShortAnswerQuestion(
                stem=f"Sample short-answer question about {skill_tag} (#{i})",
                skill_tag=skill_tag,
                prompt_version=prompt_version,
                answer=f"response-{i}",
            )
            for i in range(count)
        ]


_SCHEMA = {
    "multiple_choice": (
        'objects with "stem" (string), "options" (array of 2+ strings) and '
        '"correct_answer" (one of the options)'
    ),
    "short_answer": 'objects with "stem" (string) and "answer" (string)',
}


def _build_prompt(question_type: str, skill_tag: str, count: int) -> str:
    return (
        f"Generate {count} {question_type} assessment question(s) testing the skill "
        f'"{skill_tag}". Return ONLY a JSON array of {_SCHEMA[question_type]}. '
        "Do not put the answer verbatim in the stem. For multiple choice, "
        "keep the distractors close in length to the correct answer."
    )


def _entries_to_questions(
    entries: list[dict[str, Any]],
    *,
    question_type: str,
    skill_tag: str,
    prompt_version: str,
) -> list[Question]:
    """Turn raw LLM objects into validated questions.

    The models (``extra="forbid"``, the discriminated union) are the
    contract: anything the LLM gets wrong surfaces here as a
    ``GenerationError`` rather than a malformed document in the store.
    """
    questions: list[Question] = []
    for entry in entries:
        merged = {
            **entry,
            "type": question_type,
            "skill_tag": skill_tag,
            "prompt_version": prompt_version,
        }
        try:
            questions.append(QuestionAdapter.validate_python(merged))
        except ValidationError as exc:
            raise GenerationError(f"LLM produced an invalid question: {exc}") from exc
    return questions


class GeminiQuestionGenerator:
    """Real generator, used when a Gemini API key is configured."""

    def __init__(self, api_key: str, model: str = "gemini-3.6-flash") -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(
        self, *, question_type: str, skill_tag: str, count: int, prompt_version: str
    ) -> list[Question]:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=_build_prompt(question_type, skill_tag, count),
                config={"response_mime_type": "application/json"},
            )
            entries = json.loads(response.text or "")
        except GenerationError:
            raise
        except Exception as exc:  # noqa: BLE001 - SDK/JSON failures all become one error
            raise GenerationError(f"Gemini call failed: {exc}") from exc
        if not isinstance(entries, list):
            raise GenerationError("Gemini did not return a JSON array")
        return _entries_to_questions(
            entries,
            question_type=question_type,
            skill_tag=skill_tag,
            prompt_version=prompt_version,
        )
