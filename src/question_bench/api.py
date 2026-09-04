"""FastAPI application: the five endpoints in the brief.

The route functions stay thin - they validate input, call the store or
the harness, and shape the response. All logic lives in ``models``,
``eval``, ``llm`` and ``store``.
"""

from __future__ import annotations
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Any, Literal
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, ValidationError
from question_bench.db import lifespan
from question_bench.eval import EvaluationReport, PromptVersionStats, evaluate
from question_bench.llm import GenerationError, QuestionGenerator, StubQuestionGenerator
from question_bench.models import Question, QuestionAdapter
from question_bench.settings import Settings, get_settings
from question_bench.store import InMemoryQuestionStore, QuestionStore

# Fields the client may not change via PATCH: identity, kind, and
# provenance are set once at creation.
_PROTECTED_FIELDS = {"id", "type", "created_at", "prompt_version"}


class GenerateRequest(BaseModel):
    question_type: Literal["multiple_choice", "short_answer"]
    skill_tag: str = Field(min_length=1)
    count: int = Field(default=1, ge=1, le=10)


# --- dependency wiring --------------------------------------------------------

_memory_store = InMemoryQuestionStore()
_generator = StubQuestionGenerator()


def get_store(request: Request) -> QuestionStore:
    """Mongo-backed when the lifespan connected a client, else in-memory.

    Unit tests either skip the lifespan (so they get the in-memory store)
    or override this dependency entirely.
    """
    mongo_db = getattr(request.app.state, "mongo_db", None)
    if mongo_db is not None:
        from question_bench.mongo_store import MongoQuestionStore

        return MongoQuestionStore(mongo_db)
    return _memory_store


@lru_cache
def _gemini_generator(api_key: str) -> QuestionGenerator:
    from question_bench.llm import GeminiQuestionGenerator

    return GeminiQuestionGenerator(api_key)


def get_generator() -> QuestionGenerator:
    """Gemini when a key is configured, the deterministic stub otherwise."""
    api_key = get_settings().gemini_api_key
    return _gemini_generator(api_key) if api_key else _generator


StoreDep = Annotated[QuestionStore, Depends(get_store)]
GeneratorDep = Annotated[QuestionGenerator, Depends(get_generator)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

app = FastAPI(title="question-bench", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/generate", response_model=list[Question], status_code=status.HTTP_201_CREATED
)
async def generate(
    request: GenerateRequest,
    store: StoreDep,
    generator: GeneratorDep,
    settings: SettingsDep,
) -> list[Question]:
    try:
        questions = generator.generate(
            question_type=request.question_type,
            skill_tag=request.skill_tag,
            count=request.count,
            prompt_version=settings.prompt_version,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"question generation failed: {exc}",
        ) from exc
    return [await store.add(question) for question in questions]


@app.get("/questions", response_model=list[Question])
async def list_questions(
    store: StoreDep,
    question_type: str | None = None,
    skill_tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Question]:
    return await store.list_questions(
        question_type=question_type, skill_tag=skill_tag, limit=limit, offset=offset
    )


async def _get_or_404(store: StoreDep, question_id: str) -> Question:
    question = await store.get(question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="question not found"
        )
    return question


@app.get("/questions/{question_id}", response_model=Question)
async def get_question(question_id: str, store: StoreDep) -> Question:
    return await _get_or_404(store, question_id)


@app.patch("/questions/{question_id}", response_model=Question)
async def patch_question(
    question_id: str, body: dict[str, Any], store: StoreDep
) -> Question:
    question = await _get_or_404(store, question_id)

    protected = _PROTECTED_FIELDS & body.keys()
    if protected:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"these fields cannot be patched: {sorted(protected)}",
        )

    merged = {**question.model_dump(), **body, "updated_at": datetime.now(UTC)}
    try:
        updated = QuestionAdapter.validate_python(merged)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.errors()
        ) from exc
    return await store.replace(updated)


@app.post("/questions/{question_id}/evaluate", response_model=EvaluationReport)
async def evaluate_question(question_id: str, store: StoreDep) -> EvaluationReport:
    question = await _get_or_404(store, question_id)
    return await store.add_report(evaluate(question))


# Not one of the five endpoints in the brief, but "prompt changes show as
# pass-rate deltas" needs a reader. Kept read-only and off to the side.
@app.get("/stats/pass-rate", response_model=list[PromptVersionStats])
async def pass_rate(store: StoreDep) -> list[PromptVersionStats]:
    return await store.pass_rate_by_prompt_version()
