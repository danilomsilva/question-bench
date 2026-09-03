"""Tests for the eval harness: the result value object, the rules, the aggregator."""

from dataclasses import FrozenInstanceError

import pytest

from item_bench.eval import (
    EvaluationReport,
    RuleResult,
    distractor_length_within_30pct,
    evaluate,
    exactly_one_correct_answer,
    no_duplicate_options,
    skill_tag_allowed,
    stem_excludes_answer,
)
from item_bench.models import MultipleChoiceItem, ShortAnswerItem

# --- RuleResult ------------------------------------------------------------


def test_rule_result_detail_defaults_to_none() -> None:
    assert RuleResult(rule="x", passed=True).detail is None


def test_rule_result_is_immutable() -> None:
    result = RuleResult(rule="x", passed=True)
    with pytest.raises(FrozenInstanceError):
        result.passed = False


# --- exactly_one_correct_answer -----------------------------------------------


def test_exactly_one_correct_answer_passes_for_valid_item(
    valid_mc: MultipleChoiceItem,
) -> None:
    assert exactly_one_correct_answer(valid_mc).passed


def test_exactly_one_correct_answer_fails_when_answer_absent(
    valid_mc: MultipleChoiceItem,
) -> None:
    broken = valid_mc.model_copy(update={"correct_answer": "not an option"})

    result = exactly_one_correct_answer(broken)

    assert not result.passed
    assert "0 option" in result.detail


def test_exactly_one_correct_answer_fails_when_answer_appears_twice(
    valid_mc: MultipleChoiceItem,
) -> None:
    broken = valid_mc.model_copy(update={"options": ["7", "7", "9"]})

    assert not exactly_one_correct_answer(broken).passed


# --- no_duplicate_options ---------------------------------------------------


def test_no_duplicate_options_passes_for_valid_item(
    valid_mc: MultipleChoiceItem,
) -> None:
    assert no_duplicate_options(valid_mc).passed


def test_no_duplicate_options_fails_on_repeat(valid_mc: MultipleChoiceItem) -> None:
    broken = valid_mc.model_copy(update={"options": ["4", "6", "6", "7"]})

    result = no_duplicate_options(broken)

    assert not result.passed
    assert "'6'" in result.detail


# --- distractor_length_within_30pct --------------------------------------------


def test_distractor_length_passes_for_valid_item(valid_mc: MultipleChoiceItem) -> None:
    assert distractor_length_within_30pct(valid_mc).passed


def test_distractor_length_fails_on_a_much_longer_distractor(
    valid_mc: MultipleChoiceItem,
) -> None:
    broken = valid_mc.model_copy(
        update={"options": ["7", "a distractor that is far too long to be plausible"]}
    )

    result = distractor_length_within_30pct(broken)

    assert not result.passed
    assert "30%" in result.detail


# --- stem_excludes_answer -------------------------------------------------------


def test_stem_excludes_answer_passes_for_valid_items(
    valid_mc: MultipleChoiceItem, valid_sa: ShortAnswerItem
) -> None:
    assert stem_excludes_answer(valid_mc).passed
    assert stem_excludes_answer(valid_sa).passed


def test_stem_excludes_answer_fails_when_mc_stem_leaks_answer(
    valid_mc: MultipleChoiceItem,
) -> None:
    broken = valid_mc.model_copy(update={"stem": "Which is prime: is it 7?"})

    assert not stem_excludes_answer(broken).passed


def test_stem_excludes_answer_fails_when_sa_stem_leaks_answer(
    valid_sa: ShortAnswerItem,
) -> None:
    broken = valid_sa.model_copy(update={"stem": "What is ten divided by two (5)?"})

    assert not stem_excludes_answer(broken).passed


# --- skill_tag_allowed --------------------------------------------------------


def test_skill_tag_allowed_passes_for_valid_items(
    valid_mc: MultipleChoiceItem, valid_sa: ShortAnswerItem
) -> None:
    assert skill_tag_allowed(valid_mc).passed
    assert skill_tag_allowed(valid_sa).passed


def test_skill_tag_allowed_fails_for_unknown_tag(valid_mc: MultipleChoiceItem) -> None:
    broken = valid_mc.model_copy(update={"skill_tag": "underwater-basket-weaving"})

    result = skill_tag_allowed(broken)

    assert not result.passed
    assert "underwater-basket-weaving" in result.detail


# --- evaluate (aggregator) --------------------------------------------------


def test_evaluate_multiple_choice_all_pass(valid_mc: MultipleChoiceItem) -> None:
    report = evaluate(valid_mc)

    assert isinstance(report, EvaluationReport)
    assert len(report.results) == 5
    assert report.passed
    assert report.score == 1.0
    assert report.item_id == valid_mc.id
    assert report.prompt_version == valid_mc.prompt_version


def test_evaluate_short_answer_runs_only_two_rules(valid_sa: ShortAnswerItem) -> None:
    report = evaluate(valid_sa)

    assert {r.rule for r in report.results} == {
        "stem_excludes_answer",
        "skill_tag_allowed",
    }
    assert report.passed
    assert report.score == 1.0


def test_evaluate_reports_partial_score_and_failure(
    valid_mc: MultipleChoiceItem,
) -> None:
    broken = valid_mc.model_copy(update={"skill_tag": "nope"})

    report = evaluate(broken)

    assert not report.passed
    assert report.score == 0.8
    failed = [r for r in report.results if not r.passed]
    assert [r.rule for r in failed] == ["skill_tag_allowed"]


def test_evaluation_report_serialises(valid_mc: MultipleChoiceItem) -> None:
    dumped = evaluate(valid_mc).model_dump()

    assert dumped["score"] == 1.0
    assert dumped["results"][0]["rule"] == "exactly_one_correct_answer"
