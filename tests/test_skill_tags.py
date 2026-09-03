"""Tests for the skill-tag vocabulary."""

from item_bench.skill_tags import ALLOWED_SKILL_TAGS


def test_vocabulary_is_a_non_empty_frozenset_of_strings() -> None:
    assert isinstance(ALLOWED_SKILL_TAGS, frozenset)
    assert ALLOWED_SKILL_TAGS
    assert all(isinstance(tag, str) and tag for tag in ALLOWED_SKILL_TAGS)
