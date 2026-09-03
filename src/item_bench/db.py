"""MongoDB client lifecycle.

The motor client is created once at startup and closed at shutdown. motor
connects lazily, so building the client never fails on its own - the
first real query is what needs Mongo to be reachable. When the client is
present on ``app.state`` the dependency wiring hands routes a
``MongoItemStore``; otherwise they get the in-memory store.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from item_bench.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    # tz_aware so BSON datetimes come back as timezone-aware UTC, matching
    # how the models store them.
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongo_url, tz_aware=True)
    app.state.mongo_client = client
    app.state.mongo_db = client[settings.mongo_db]
    try:
        yield
    finally:
        client.close()
