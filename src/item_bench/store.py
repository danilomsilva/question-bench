"""Persistence boundary.

``ItemStore`` is a Protocol, not a base class: the in-memory store here
and the MongoDB store in Step 5 just have to match its shape, nothing
inherits. The API depends on the Protocol, so swapping implementations is
a one-line change in the dependency wiring.
"""

from __future__ import annotations

from typing import Protocol

from item_bench.eval import EvaluationReport
from item_bench.models import Item


class ItemStore(Protocol):
    def add(self, item: Item) -> Item: ...

    def get(self, item_id: str) -> Item | None: ...

    def list_items(
        self,
        *,
        item_type: str | None = None,
        skill_tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]: ...

    def replace(self, item: Item) -> Item: ...

    def add_report(self, report: EvaluationReport) -> EvaluationReport: ...

    def list_reports(self, item_id: str) -> list[EvaluationReport]: ...


class InMemoryItemStore:
    """Dict-backed store. Insertion order is preserved by ``dict``."""

    def __init__(self) -> None:
        self._items: dict[str, Item] = {}
        self._reports: list[EvaluationReport] = []

    def add(self, item: Item) -> Item:
        self._items[item.id] = item
        return item

    def get(self, item_id: str) -> Item | None:
        return self._items.get(item_id)

    def list_items(
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

    def replace(self, item: Item) -> Item:
        self._items[item.id] = item
        return item

    def add_report(self, report: EvaluationReport) -> EvaluationReport:
        self._reports.append(report)
        return report

    def list_reports(self, item_id: str) -> list[EvaluationReport]:
        return [r for r in self._reports if r.item_id == item_id]
