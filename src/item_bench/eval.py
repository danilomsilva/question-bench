"""Deterministic quality checks for assessment items.

Each rule is a function that takes an item and returns a ``RuleResult``.
The aggregator (added later) runs the rules that apply to an item's type
and produces an overall score. These checks are structural and
rule-based, deliberately not an LLM-as-judge.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuleResult:
    """Outcome of a single rule applied to a single item.

    Frozen because a result is a fact about a past check, not something
    to edit afterwards.
    """

    rule: str
    passed: bool
    detail: str | None = None
