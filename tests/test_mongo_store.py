"""Integration tests for MongoItemStore against a real MongoDB.

Skipped automatically when no Mongo is reachable at ``MONGO_URL``
(default ``mongodb://localhost:27017``). CI provides one as a service
container; locally, ``docker compose up -d mongo``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pymongo
import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from item_bench.db import ensure_indexes
from item_bench.eval import evaluate
from item_bench.models import MultipleChoiceItem, ShortAnswerItem
from item_bench.mongo_store import MongoItemStore

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")


def _mongo_available() -> bool:
    try:
        client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        client.close()
        return True
    except Exception:  # noqa: BLE001 - any failure means "not available"
        return False


# Evaluated once at collection time, so the connection timeout is paid once.
pytestmark = [
    pytest.mark.mongo,
    pytest.mark.skipif(not _mongo_available(), reason=f"no MongoDB at {MONGO_URL}"),
]


@pytest_asyncio.fixture
async def mongo_db() -> AsyncIterator[AsyncIOMotorDatabase]:
    client = AsyncIOMotorClient(MONGO_URL, tz_aware=True)
    db = client["item_bench_test"]
    for name in ("items", "evaluations"):
        await db[name].delete_many({})
    yield db
    await client.drop_database("item_bench_test")
    client.close()


@pytest.fixture
def store(mongo_db: AsyncIOMotorDatabase) -> MongoItemStore:
    return MongoItemStore(mongo_db)


async def test_add_then_get(
    store: MongoItemStore, valid_mc: MultipleChoiceItem
) -> None:
    await store.add(valid_mc)

    fetched = await store.get(valid_mc.id)

    assert isinstance(fetched, MultipleChoiceItem)
    assert fetched.stem == valid_mc.stem
    assert fetched.options == valid_mc.options
    assert fetched.created_at.tzinfo is not None


async def test_get_missing_returns_none(store: MongoItemStore) -> None:
    assert await store.get("nope") is None


async def test_round_trip_preserves_fields(
    store: MongoItemStore, valid_mc: MultipleChoiceItem
) -> None:
    await store.add(valid_mc)

    fetched = await store.get(valid_mc.id)
    assert fetched is not None

    ignore = {"created_at", "updated_at"}
    assert fetched.model_dump(exclude=ignore) == valid_mc.model_dump(exclude=ignore)
    # BSON datetimes are millisecond precision, so allow sub-ms drift.
    assert abs((fetched.created_at - valid_mc.created_at).total_seconds()) < 0.001


async def test_short_answer_round_trip(
    store: MongoItemStore, valid_sa: ShortAnswerItem
) -> None:
    await store.add(valid_sa)

    fetched = await store.get(valid_sa.id)

    assert isinstance(fetched, ShortAnswerItem)
    assert fetched.answer == valid_sa.answer


async def test_list_filters_and_paginates(
    store: MongoItemStore, valid_mc: MultipleChoiceItem
) -> None:
    await store.add(
        valid_mc.model_copy(update={"id": "mc-1", "skill_tag": "arithmetic"})
    )
    await store.add(valid_mc.model_copy(update={"id": "mc-2", "skill_tag": "algebra"}))
    await store.add(valid_mc.model_copy(update={"id": "mc-3", "skill_tag": "algebra"}))

    assert len(await store.list_items()) == 3
    assert len(await store.list_items(skill_tag="algebra")) == 2
    assert len(await store.list_items(limit=2)) == 2
    assert len(await store.list_items(offset=2)) == 1


async def test_replace_persists(
    store: MongoItemStore, valid_mc: MultipleChoiceItem
) -> None:
    await store.add(valid_mc)

    await store.replace(valid_mc.model_copy(update={"stem": "A replacement stem"}))

    fetched = await store.get(valid_mc.id)
    assert fetched is not None
    assert fetched.stem == "A replacement stem"


async def test_reports_add_and_list(
    store: MongoItemStore, valid_mc: MultipleChoiceItem
) -> None:
    await store.add(valid_mc)
    await store.add_report(evaluate(valid_mc))

    reports = await store.list_reports(valid_mc.id)

    assert len(reports) == 1
    assert reports[0].item_id == valid_mc.id
    assert reports[0].score == 1.0


async def test_pass_rate_by_prompt_version(
    store: MongoItemStore, valid_mc: MultipleChoiceItem
) -> None:
    await store.add_report(evaluate(valid_mc))
    await store.add_report(evaluate(valid_mc.model_copy(update={"skill_tag": "nope"})))

    stats = await store.pass_rate_by_prompt_version()

    assert len(stats) == 1
    assert stats[0].prompt_version == valid_mc.prompt_version
    assert stats[0].evaluations == 2
    assert stats[0].passed == 1
    assert stats[0].pass_rate == 0.5


async def test_ensure_indexes_is_idempotent(mongo_db: AsyncIOMotorDatabase) -> None:
    await ensure_indexes(mongo_db)
    await ensure_indexes(mongo_db)  # second call must not raise

    item_indexes = await mongo_db["items"].index_information()
    indexed_fields = {spec["key"][0][0] for spec in item_indexes.values()}
    assert {"type", "skill_tag", "prompt_version", "created_at"} <= indexed_fields
