"""Persistence boundary.

``QuestionStore`` is a Protocol, not a base class: the in-memory store here
and the MongoDB store in ``mongo_store`` just have to match its shape,
nothing inherits. The API depends on the Protocol, so swapping
implementations is a one-line change in the dependency wiring.

The methods are ``async`` because the real implementation (motor) is
async; the in-memory store simply doesn't await anything.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Protocol
from question_bench.eval import EvaluationReport, PromptVersionStats
from question_bench.models import Question


class QuestionStore(Protocol):
    async def add(self, question: Question) -> Question: ...

    async def get(self, question_id: str) -> Question | None: ...

    async def list_questions(
        self,
        *,
        question_type: str | None = None,
        topic: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Question]: ...

    async def replace(self, question: Question) -> Question: ...

    async def add_report(self, report: EvaluationReport) -> EvaluationReport: ...

    async def list_reports(self, question_id: str) -> list[EvaluationReport]: ...

    async def pass_rate_by_prompt_version(self) -> list[PromptVersionStats]: ...


class InMemoryQuestionStore:
    """Dict-backed store. Insertion order is preserved by ``dict``."""

    def __init__(self) -> None:
        self._questions: dict[str, Question] = {}
        self._reports: list[EvaluationReport] = []

    async def add(self, question: Question) -> Question:
        self._questions[question.id] = question
        return question

    async def get(self, question_id: str) -> Question | None:
        return self._questions.get(question_id)

    async def list_questions(
        self,
        *,
        question_type: str | None = None,
        topic: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Question]:
        questions = list(self._questions.values())
        if question_type is not None:
            questions = [i for i in questions if i.type == question_type]
        if topic is not None:
            questions = [i for i in questions if i.topic == topic]
        return questions[offset : offset + limit]

    async def replace(self, question: Question) -> Question:
        self._questions[question.id] = question
        return question

    async def add_report(self, report: EvaluationReport) -> EvaluationReport:
        self._reports.append(report)
        return report

    async def list_reports(self, question_id: str) -> list[EvaluationReport]:
        return [r for r in self._reports if r.question_id == question_id]

    async def pass_rate_by_prompt_version(self) -> list[PromptVersionStats]:
        by_version: dict[str, list[EvaluationReport]] = defaultdict(list)
        for report in self._reports:
            by_version[report.prompt_version].append(report)
        stats = []
        for version, reports in sorted(by_version.items()):
            passed = sum(1 for r in reports if r.passed)
            stats.append(
                PromptVersionStats(
                    prompt_version=version,
                    evaluations=len(reports),
                    passed=passed,
                    pass_rate=passed / len(reports),
                )
            )
        return stats
