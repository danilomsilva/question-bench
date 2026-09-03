"""FastAPI application: the five endpoints in the brief.

The route functions stay thin - they validate input, call the store or
the harness, and shape the response. All logic lives in ``models``,
``eval``, ``llm`` and ``store``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, ValidationError

from item_bench.db import lifespan
from item_bench.eval import EvaluationReport, PromptVersionStats, evaluate
from item_bench.llm import GenerationError, ItemGenerator, StubItemGenerator
from item_bench.models import Item, ItemAdapter
from item_bench.settings import Settings, get_settings
from item_bench.store import InMemoryItemStore, ItemStore

# Fields the client may not change via PATCH: identity, kind, and
# provenance are set once at creation.
_PROTECTED_FIELDS = {"id", "type", "created_at", "prompt_version"}


class GenerateRequest(BaseModel):
    item_type: Literal["multiple_choice", "short_answer"]
    skill_tag: str = Field(min_length=1)
    count: int = Field(default=1, ge=1, le=10)


# --- dependency wiring --------------------------------------------------------

_memory_store = InMemoryItemStore()
_generator = StubItemGenerator()


def get_store(request: Request) -> ItemStore:
    """Mongo-backed when the lifespan connected a client, else in-memory.

    Unit tests either skip the lifespan (so they get the in-memory store)
    or override this dependency entirely.
    """
    mongo_db = getattr(request.app.state, "mongo_db", None)
    if mongo_db is not None:
        from item_bench.mongo_store import MongoItemStore

        return MongoItemStore(mongo_db)
    return _memory_store


def get_generator() -> ItemGenerator:
    return _generator


StoreDep = Annotated[ItemStore, Depends(get_store)]
GeneratorDep = Annotated[ItemGenerator, Depends(get_generator)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

app = FastAPI(title="item-bench", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate", response_model=list[Item], status_code=status.HTTP_201_CREATED)
async def generate(
    request: GenerateRequest,
    store: StoreDep,
    generator: GeneratorDep,
    settings: SettingsDep,
) -> list[Item]:
    try:
        items = generator.generate(
            item_type=request.item_type,
            skill_tag=request.skill_tag,
            count=request.count,
            prompt_version=settings.prompt_version,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"item generation failed: {exc}",
        ) from exc
    return [await store.add(item) for item in items]


@app.get("/items", response_model=list[Item])
async def list_items(
    store: StoreDep,
    item_type: str | None = None,
    skill_tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Item]:
    return await store.list_items(
        item_type=item_type, skill_tag=skill_tag, limit=limit, offset=offset
    )


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str, store: StoreDep) -> Item:
    item = await store.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )
    return item


@app.patch("/items/{item_id}", response_model=Item)
async def patch_item(item_id: str, body: dict[str, Any], store: StoreDep) -> Item:
    item = await store.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )

    protected = _PROTECTED_FIELDS & body.keys()
    if protected:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"these fields cannot be patched: {sorted(protected)}",
        )

    merged = {**item.model_dump(), **body, "updated_at": datetime.now(UTC)}
    try:
        updated = ItemAdapter.validate_python(merged)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.errors()
        ) from exc
    return await store.replace(updated)


@app.post("/items/{item_id}/evaluate", response_model=EvaluationReport)
async def evaluate_item(item_id: str, store: StoreDep) -> EvaluationReport:
    item = await store.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )
    return await store.add_report(evaluate(item))


# Not one of the five endpoints in the brief, but "prompt changes show as
# pass-rate deltas" needs a reader. Kept read-only and off to the side.
@app.get("/stats/pass-rate", response_model=list[PromptVersionStats])
async def pass_rate(store: StoreDep) -> list[PromptVersionStats]:
    return await store.pass_rate_by_prompt_version()
