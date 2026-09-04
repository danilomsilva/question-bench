"""Deterministic quality checks for assessment questions.

Each rule is a function that takes a question and returns a ``RuleResult``.
The aggregator (added later) runs the rules that apply to a question's type
and produces an overall score. These checks are structural and
rule-based, deliberately not an LLM-as-judge.
"""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pydantic import BaseModel, Field
from question_bench.models import MultipleChoiceQuestion, Question, ShortAnswerQuestion
from question_bench.skill_tags import ALLOWED_SKILL_TAGS


@dataclass(frozen=True, slots=True)
class RuleResult:
    """Outcome of a single rule applied to a single question.

    Frozen because a result is a fact about a past check, not something
    to edit afterwards.
    """

    rule: str
    passed: bool
    detail: str | None = None


def exactly_one_correct_answer(question: MultipleChoiceQuestion) -> RuleResult:
    """Exactly one option must equal ``correct_answer``.

    Zero matches means the answer isn't offered; two or more means it's
    ambiguous (and usually implies duplicate options too).
    """
    matches = question.options.count(question.correct_answer)
    if matches == 1:
        return RuleResult(rule="exactly_one_correct_answer", passed=True)
    detail = f"correct_answer {question.correct_answer!r} matches {matches} option(s)"
    return RuleResult(rule="exactly_one_correct_answer", passed=False, detail=detail)


def no_duplicate_options(question: MultipleChoiceQuestion) -> RuleResult:
    """Every option string must be distinct."""
    counts = Counter(question.options)
    dupes = sorted(option for option, n in counts.items() if n > 1)
    if not dupes:
        return RuleResult(rule="no_duplicate_options", passed=True)
    detail = f"duplicated option(s): {', '.join(map(repr, dupes))}"
    return RuleResult(rule="no_duplicate_options", passed=False, detail=detail)


def distractor_length_within_30pct(question: MultipleChoiceQuestion) -> RuleResult:
    """Every distractor's length must be within +/-30% of the correct answer's.

    Distractors that are much shorter or longer than the key are a
    giveaway. Distractors are the options that aren't the correct answer.
    """
    correct_len = len(question.correct_answer)
    low, high = 0.7 * correct_len, 1.3 * correct_len
    distractors = (o for o in question.options if o != question.correct_answer)
    offenders = sorted({o for o in distractors if not low <= len(o) <= high})
    if not offenders:
        return RuleResult(rule="distractor_length_within_30pct", passed=True)
    detail = (
        f"length outside +/-30% of {correct_len}: {', '.join(map(repr, offenders))}"
    )
    return RuleResult(
        rule="distractor_length_within_30pct", passed=False, detail=detail
    )


def stem_excludes_answer(
    question: MultipleChoiceQuestion | ShortAnswerQuestion,
) -> RuleResult:
    """The stem must not contain the answer verbatim (case-sensitive)."""
    if isinstance(question, MultipleChoiceQuestion):
        answer = question.correct_answer
    else:
        answer = question.answer
    if answer not in question.stem:
        return RuleResult(rule="stem_excludes_answer", passed=True)
    detail = f"stem contains the answer {answer!r} verbatim"
    return RuleResult(rule="stem_excludes_answer", passed=False, detail=detail)


def skill_tag_allowed(
    question: MultipleChoiceQuestion | ShortAnswerQuestion,
) -> RuleResult:
    """The question's ``skill_tag`` must be in the allowed vocabulary."""
    if question.skill_tag in ALLOWED_SKILL_TAGS:
        return RuleResult(rule="skill_tag_allowed", passed=True)
    detail = f"{question.skill_tag!r} is not an allowed skill tag"
    return RuleResult(rule="skill_tag_allowed", passed=False, detail=detail)


class EvaluationReport(BaseModel):
    """The outcome of running every applicable rule over one question.

    ``score`` is the fraction of applicable rules that passed (0.0-1.0),
    so multiple-choice and short-answer questions stay comparable even though
    a different number of rules applies to each. Stored against
    ``prompt_version`` so prompt changes surface as pass-rate deltas.
    """

    question_id: str
    prompt_version: str
    results: list[RuleResult]
    passed: bool
    score: float
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PromptVersionStats(BaseModel):
    """Pass rate for every question ever evaluated under one prompt version.

    This is the headline number: change the generation prompt, re-run the
    evaluations, and compare ``pass_rate`` across versions.
    """

    prompt_version: str
    evaluations: int
    passed: int
    pass_rate: float


def evaluate(question: Question) -> EvaluationReport:
    """Run the rules that apply to this question's type and score the question."""
    if isinstance(question, MultipleChoiceQuestion):
        results = [
            exactly_one_correct_answer(question),
            no_duplicate_options(question),
            distractor_length_within_30pct(question),
            stem_excludes_answer(question),
            skill_tag_allowed(question),
        ]
    else:
        # Short answer: no options, and a single answer field, so only the
        # two type-agnostic rules apply.
        results = [
            stem_excludes_answer(question),
            skill_tag_allowed(question),
        ]

    passed_count = sum(1 for r in results if r.passed)
    return EvaluationReport(
        question_id=question.id,
        prompt_version=question.prompt_version,
        results=results,
        passed=passed_count == len(results),
        score=passed_count / len(results),
    )
