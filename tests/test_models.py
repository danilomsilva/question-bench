"""Tests for the item models."""

import pytest
from pydantic import ValidationError

from item_bench.models import (
    ItemAdapter,
    ItemBase,
    MultipleChoiceItem,
    ShortAnswerItem,
)


def _valid_kwargs() -> dict[str, str]:
    return {"stem": "What is 2 + 2?", "skill_tag": "arithmetic", "prompt_version": "v1"}


def test_defaults_are_populated() -> None:
    item = ItemBase(**_valid_kwargs())

    assert len(item.id) == 32
    assert item.created_at.tzinfo is not None
    assert item.updated_at >= item.created_at


def test_blank_required_string_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ItemBase(**{**_valid_kwargs(), "stem": ""})


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ItemBase(**{**_valid_kwargs(), "difficulty": "hard"})


def _valid_mc_kwargs() -> dict[str, object]:
    return {
        **_valid_kwargs(),
        "options": ["3", "4", "5"],
        "correct_answer": "4",
    }


def test_multiple_choice_valid() -> None:
    item = MultipleChoiceItem(**_valid_mc_kwargs())

    assert item.type == "multiple_choice"
    assert len(item.id) == 32
    assert item.options == ["3", "4", "5"]


def test_multiple_choice_requires_at_least_two_options() -> None:
    with pytest.raises(ValidationError):
        MultipleChoiceItem(**{**_valid_mc_kwargs(), "options": ["only one"]})


def test_multiple_choice_allows_answer_not_in_options() -> None:
    # Shape is valid; "exactly one correct answer" is the harness's job.
    item = MultipleChoiceItem(**{**_valid_mc_kwargs(), "correct_answer": "42"})

    assert item.correct_answer == "42"


def test_short_answer_valid() -> None:
    item = ShortAnswerItem(**_valid_kwargs(), answer="4")

    assert item.type == "short_answer"
    assert item.answer == "4"
    assert len(item.id) == 32


def test_short_answer_requires_non_blank_answer() -> None:
    with pytest.raises(ValidationError):
        ShortAnswerItem(**_valid_kwargs(), answer="")


def test_short_answer_rejects_multiple_choice_fields() -> None:
    with pytest.raises(ValidationError):
        ShortAnswerItem(**_valid_kwargs(), answer="4", options=["3", "4"])


def test_adapter_routes_multiple_choice() -> None:
    item = ItemAdapter.validate_python(
        {
            **_valid_kwargs(),
            "type": "multiple_choice",
            "options": ["3", "4"],
            "correct_answer": "4",
        }
    )

    assert isinstance(item, MultipleChoiceItem)


def test_adapter_routes_short_answer() -> None:
    item = ItemAdapter.validate_python(
        {**_valid_kwargs(), "type": "short_answer", "answer": "4"}
    )

    assert isinstance(item, ShortAnswerItem)


def test_adapter_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        ItemAdapter.validate_python({**_valid_kwargs(), "type": "essay", "answer": "x"})


def test_adapter_rejects_missing_type() -> None:
    with pytest.raises(ValidationError):
        ItemAdapter.validate_python({**_valid_kwargs(), "answer": "4"})


def test_round_trip_multiple_choice(valid_mc: MultipleChoiceItem) -> None:
    dumped = ItemAdapter.dump_python(valid_mc)
    reparsed = ItemAdapter.validate_python(dumped)

    assert reparsed == valid_mc


def test_round_trip_short_answer(valid_sa: ShortAnswerItem) -> None:
    dumped = ItemAdapter.dump_python(valid_sa)
    reparsed = ItemAdapter.validate_python(dumped)

    assert reparsed == valid_sa
