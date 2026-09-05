"""Tests for the LLM generation seam - the parts that need no network.

The Gemini HTTP call itself isn't tested (no key in CI); the valuable
logic is turning raw model output into validated questions, which is pure.
"""

import pytest
from question_bench.llm import GenerationError, _build_prompt, _entries_to_questions


def test_build_prompt_names_type_skill_and_count() -> None:
    prompt = _build_prompt("multiple_choice", "fractions", 3)

    assert "3" in prompt
    assert "multiple_choice" in prompt
    assert "fractions" in prompt


def test_entries_to_questions_validates_and_stamps_provenance() -> None:
    questions = _entries_to_questions(
        [{"stem": "Pick one", "options": ["aa", "bb", "cc"], "correct_answer": "bb"}],
        question_type="multiple_choice",
        topic="arithmetic",
        prompt_version="gemini-test",
    )

    assert len(questions) == 1
    assert questions[0].topic == "arithmetic"
    assert questions[0].prompt_version == "gemini-test"


def test_entries_to_questions_rejects_missing_field() -> None:
    with pytest.raises(GenerationError):
        _entries_to_questions(
            [{"stem": "no options here"}],
            question_type="multiple_choice",
            topic="arithmetic",
            prompt_version="x",
        )


def test_entries_to_questions_rejects_extra_field() -> None:
    with pytest.raises(GenerationError):
        _entries_to_questions(
            [{"stem": "q", "answer": "a", "difficulty": "hard"}],
            question_type="short_answer",
            topic="arithmetic",
            prompt_version="x",
        )
