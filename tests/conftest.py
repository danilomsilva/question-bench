"""Shared fixtures: a known-good item of each type.

These pass every eval rule (added in Step 3). Tests that need a
rule-violating item build one by copying a fixture with a bad field.
"""

import pytest

from item_bench.models import MultipleChoiceItem, ShortAnswerItem


@pytest.fixture
def valid_mc() -> MultipleChoiceItem:
    return MultipleChoiceItem(
        stem="Which number is prime?",
        skill_tag="arithmetic",
        prompt_version="v1",
        options=["4", "6", "7", "9"],
        correct_answer="7",
    )


@pytest.fixture
def valid_sa() -> ShortAnswerItem:
    return ShortAnswerItem(
        stem="What is ten divided by two?",
        skill_tag="arithmetic",
        prompt_version="v1",
        answer="5",
    )
