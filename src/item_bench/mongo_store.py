"""MongoDB-backed :class:`item_bench.store.ItemStore`.

One collection per concern: ``items`` and ``evaluations``. The item's
own uuid is used as the Mongo ``_id`` (decided in the data-model step),
so there is no second identifier to keep in sync.

(De)serialisation is deliberately simple: ``model_dump(mode="python")``
keeps ``datetime`` objects, which BSON stores natively so ``created_at``
range queries work; on the way back the discriminated ``ItemAdapter``
re-parses and re-validates every document.
"""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from item_bench.eval import EvaluationReport, PromptVersionStats
from item_bench.models import Item, ItemAdapter


def _to_doc(item: Item) -> dict[str, Any]:
    doc = item.model_dump(mode="python", exclude={"id"})
    doc["_id"] = item.id
    return doc


def _from_doc(doc: dict[str, Any]) -> Item:
    raw = {key: value for key, value in doc.items() if key != "_id"}
    raw["id"] = doc["_id"]
    return ItemAdapter.validate_python(raw)


class MongoItemStore:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._items = db["items"]
        self._reports = db["evaluations"]

    async def add(self, item: Item) -> Item:
        await self._items.insert_one(_to_doc(item))
        return item

    async def get(self, item_id: str) -> Item | None:
        doc = await self._items.find_one({"_id": item_id})
        return _from_doc(doc) if doc is not None else None

    async def list_items(
        self,
        *,
        item_type: str | None = None,
        skill_tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Item]:
        query: dict[str, Any] = {}
        if item_type is not None:
            query["type"] = item_type
        if skill_tag is not None:
            query["skill_tag"] = skill_tag
        cursor = self._items.find(query).sort("created_at", 1).skip(offset).limit(limit)
        return [_from_doc(doc) for doc in await cursor.to_list(length=limit)]

    async def replace(self, item: Item) -> Item:
        await self._items.replace_one({"_id": item.id}, _to_doc(item))
        return item

    async def add_report(self, report: EvaluationReport) -> EvaluationReport:
        await self._reports.insert_one(report.model_dump(mode="python"))
        return report

    async def list_reports(self, item_id: str) -> list[EvaluationReport]:
        cursor = self._reports.find({"item_id": item_id}).sort("evaluated_at", 1)
        docs = await cursor.to_list(length=None)
        return [
            EvaluationReport.model_validate(
                {key: value for key, value in doc.items() if key != "_id"}
            )
            for doc in docs
        ]

    async def pass_rate_by_prompt_version(self) -> list[PromptVersionStats]:
        pipeline = [
            {
                "$group": {
                    "_id": "$prompt_version",
                    "evaluations": {"$sum": 1},
                    "passed": {"$sum": {"$cond": ["$passed", 1, 0]}},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        rows = await self._reports.aggregate(pipeline).to_list(length=None)
        return [
            PromptVersionStats(
                prompt_version=row["_id"],
                evaluations=row["evaluations"],
                passed=row["passed"],
                pass_rate=row["passed"] / row["evaluations"],
            )
            for row in rows
        ]
