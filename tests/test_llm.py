"""Tests for the LLM generation seam - the parts that need no network.

The Gemini HTTP call itself isn't tested (no key in CI); the valuable
logic is turning raw model output into validated items, which is pure.
"""

import pytest

from item_bench.llm import GenerationError, _build_prompt, _entries_to_items


def test_build_prompt_names_type_skill_and_count() -> None:
    prompt = _build_prompt("multiple_choice", "fractions", 3)

    assert "3" in prompt
    assert "multiple_choice" in prompt
    assert "fractions" in prompt


def test_entries_to_items_validates_and_stamps_provenance() -> None:
    items = _entries_to_items(
        [{"stem": "Pick one", "options": ["aa", "bb", "cc"], "correct_answer": "bb"}],
        item_type="multiple_choice",
        skill_tag="arithmetic",
        prompt_version="gemini-test",
    )

    assert len(items) == 1
    assert items[0].skill_tag == "arithmetic"
    assert items[0].prompt_version == "gemini-test"


def test_entries_to_items_rejects_missing_field() -> None:
    with pytest.raises(GenerationError):
        _entries_to_items(
            [{"stem": "no options here"}],
            item_type="multiple_choice",
            skill_tag="arithmetic",
            prompt_version="x",
        )


def test_entries_to_items_rejects_extra_field() -> None:
    with pytest.raises(GenerationError):
        _entries_to_items(
            [{"stem": "q", "answer": "a", "difficulty": "hard"}],
            item_type="short_answer",
            skill_tag="arithmetic",
            prompt_version="x",
        )
