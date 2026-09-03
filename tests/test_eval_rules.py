"""Tests for the eval harness: the result value object, the rules, the aggregator."""

from dataclasses import FrozenInstanceError

import pytest

from item_bench.eval import RuleResult


def test_rule_result_detail_defaults_to_none() -> None:
    assert RuleResult(rule="x", passed=True).detail is None


def test_rule_result_is_immutable() -> None:
    result = RuleResult(rule="x", passed=True)
    with pytest.raises(FrozenInstanceError):
        result.passed = False
