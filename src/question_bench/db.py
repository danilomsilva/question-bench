"""MongoDB client lifecycle.

The motor client is created once at startup and closed at shutdown. motor
connects lazily, so building the client never fails on its own - the
first real query is what needs Mongo to be reachable. When the client is
present on ``app.state`` the dependency wiring hands routes a
``MongoQuestionStore``; otherwise they get the in-memory store.
"""

from __future__ import annotations
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from question_bench.settings import get_settings

# Fields the app filters, groups or sorts on. `prompt_version` matters
# most: pass-rate-by-prompt is the whole point of the eval scores.
_QUESTION_INDEXES = ("type", "skill_tag", "prompt_version", "created_at")
_EVALUATION_INDEXES = ("question_id", "prompt_version", "evaluated_at")


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Idempotent; safe to call on every startup."""
    for field in _QUESTION_INDEXES:
        await db["questions"].create_index(field)
    for field in _EVALUATION_INDEXES:
        await db["evaluations"].create_index(field)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    # tz_aware so BSON datetimes come back as timezone-aware UTC, matching
    # how the models store them.
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongo_url, tz_aware=True)
    db = client[settings.mongo_db]
    app.state.mongo_client = client
    app.state.mongo_db = db
    await ensure_indexes(db)
    try:
        yield
    finally:
        client.close()
