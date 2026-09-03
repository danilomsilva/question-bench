"""Persistence boundary.

``ItemStore`` is a Protocol, not a base class: the in-memory store here
and the MongoDB store in ``mongo_store`` just have to match its shape,
nothing inherits. The API depends on the Protocol, so swapping
implementations is a one-line change in the dependency wiring.

The methods are ``async`` because the real implementation (motor) is
async; the in-memory store simply doesn't await anything.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from item_bench.eval import EvaluationReport, PromptVersionStats
from item_bench.models import Item


class ItemStore(Protocol):
    async def add(self, item: Item) -> Item: ...

    async def get(self, item_id: str) -> Item | None: ...

    async def list_items(
        self,
        *,
        item_type: str | None = None,
        skill_tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]: ...

    async def replace(self, item: Item) -> Item: ...

    async def add_report(self, report: EvaluationReport) -> EvaluationReport: ...

    async def list_reports(self, item_id: str) -> list[EvaluationReport]: ...

    async def pass_rate_by_prompt_version(self) -> list[PromptVersionStats]: ...


class InMemoryItemStore:
    """Dict-backed store. Insertion order is preserved by ``dict``."""

    def __init__(self) -> None:
        self._items: dict[str, Item] = {}
        self._reports: list[EvaluationReport] = []

    async def add(self, item: Item) -> Item:
        self._items[item.id] = item
        return item

    async def get(self, item_id: str) -> Item | None:
        return self._items.get(item_id)

    async def list_items(
        self,
        *,
        item_type: str | None = None,
        skill_tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]:
        items = list(self._items.values())
        if item_type is not None:
            items = [i for i in items if i.type == item_type]
        if skill_tag is not None:
            items = [i for i in items if i.skill_tag == skill_tag]
        return items[offset : offset + limit]

    async def replace(self, item: Item) -> Item:
        self._items[item.id] = item
        return item

    async def add_report(self, report: EvaluationReport) -> EvaluationReport:
        self._reports.append(report)
        return report

    async def list_reports(self, item_id: str) -> list[EvaluationReport]:
        return [r for r in self._reports if r.item_id == item_id]

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
