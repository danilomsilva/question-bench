"""Tests for the item models."""

import pytest
from pydantic import ValidationError

from item_bench.models import ItemBase


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
