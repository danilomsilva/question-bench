"""Tests for the topic vocabulary."""

from question_bench.topics import ALLOWED_TOPICS


def test_vocabulary_is_a_non_empty_frozenset_of_strings() -> None:
    assert isinstance(ALLOWED_TOPICS, frozenset)
    assert ALLOWED_TOPICS
    assert all(isinstance(topic, str) and topic for topic in ALLOWED_TOPICS)
