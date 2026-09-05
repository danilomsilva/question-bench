"""Shared fixtures: a known-good question of each type.

These pass every eval rule (added in Step 3). Tests that need a
rule-violating question build one by copying a fixture with a bad field.
"""

import pytest
from question_bench.models import MultipleChoiceQuestion, ShortAnswerQuestion


@pytest.fixture
def valid_mc() -> MultipleChoiceQuestion:
    return MultipleChoiceQuestion(
        stem="Which number is prime?",
        topic="arithmetic",
        prompt_version="v1",
        options=["4", "6", "7", "9"],
        correct_answer="7",
    )


@pytest.fixture
def valid_sa() -> ShortAnswerQuestion:
    return ShortAnswerQuestion(
        stem="What is ten divided by two?",
        topic="arithmetic",
        prompt_version="v1",
        answer="5",
    )
