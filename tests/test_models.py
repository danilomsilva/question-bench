"""Tests for the question models."""

import pytest
from pydantic import ValidationError
from question_bench.models import (
    MultipleChoiceQuestion,
    QuestionAdapter,
    QuestionBase,
    ShortAnswerQuestion,
)


def _valid_kwargs() -> dict[str, str]:
    return {"stem": "What is 2 + 2?", "topic": "arithmetic", "prompt_version": "v1"}


def test_defaults_are_populated() -> None:
    question = QuestionBase(**_valid_kwargs())

    assert len(question.id) == 32
    assert question.created_at.tzinfo is not None
    assert question.updated_at >= question.created_at


def test_blank_required_string_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QuestionBase(**{**_valid_kwargs(), "stem": ""})


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QuestionBase(**{**_valid_kwargs(), "difficulty": "hard"})


def _valid_mc_kwargs() -> dict[str, object]:
    return {
        **_valid_kwargs(),
        "options": ["3", "4", "5"],
        "correct_answer": "4",
    }


def test_multiple_choice_valid() -> None:
    question = MultipleChoiceQuestion(**_valid_mc_kwargs())

    assert question.type == "multiple_choice"
    assert len(question.id) == 32
    assert question.options == ["3", "4", "5"]


def test_multiple_choice_requires_at_least_two_options() -> None:
    with pytest.raises(ValidationError):
        MultipleChoiceQuestion(**{**_valid_mc_kwargs(), "options": ["only one"]})


def test_multiple_choice_allows_answer_not_in_options() -> None:
    # Shape is valid; "exactly one correct answer" is the harness's job.
    question = MultipleChoiceQuestion(**{**_valid_mc_kwargs(), "correct_answer": "42"})

    assert question.correct_answer == "42"


def test_short_answer_valid() -> None:
    question = ShortAnswerQuestion(**_valid_kwargs(), answer="4")

    assert question.type == "short_answer"
    assert question.answer == "4"
    assert len(question.id) == 32


def test_short_answer_requires_non_blank_answer() -> None:
    with pytest.raises(ValidationError):
        ShortAnswerQuestion(**_valid_kwargs(), answer="")


def test_short_answer_rejects_multiple_choice_fields() -> None:
    with pytest.raises(ValidationError):
        ShortAnswerQuestion(**_valid_kwargs(), answer="4", options=["3", "4"])


def test_adapter_routes_multiple_choice() -> None:
    question = QuestionAdapter.validate_python(
        {
            **_valid_kwargs(),
            "type": "multiple_choice",
            "options": ["3", "4"],
            "correct_answer": "4",
        }
    )

    assert isinstance(question, MultipleChoiceQuestion)


def test_adapter_routes_short_answer() -> None:
    question = QuestionAdapter.validate_python(
        {**_valid_kwargs(), "type": "short_answer", "answer": "4"}
    )

    assert isinstance(question, ShortAnswerQuestion)


def test_adapter_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        QuestionAdapter.validate_python(
            {**_valid_kwargs(), "type": "essay", "answer": "x"}
        )


def test_adapter_rejects_missing_type() -> None:
    with pytest.raises(ValidationError):
        QuestionAdapter.validate_python({**_valid_kwargs(), "answer": "4"})


def test_round_trip_multiple_choice(valid_mc: MultipleChoiceQuestion) -> None:
    dumped = QuestionAdapter.dump_python(valid_mc)
    reparsed = QuestionAdapter.validate_python(dumped)

    assert reparsed == valid_mc


def test_round_trip_short_answer(valid_sa: ShortAnswerQuestion) -> None:
    dumped = QuestionAdapter.dump_python(valid_sa)
    reparsed = QuestionAdapter.validate_python(dumped)

    assert reparsed == valid_sa
