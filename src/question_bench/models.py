"""Pydantic models for assessment questions.

Questions are a discriminated union of concrete types (added in 2c/2d) that
share the fields defined here on ``QuestionBase``.
"""

from __future__ import annotations
import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class QuestionBase(BaseModel):
    """Fields common to every question type.

    ``extra="forbid"`` so unexpected keys (e.g. from LLM output drift)
    raise a validation error instead of being silently ignored.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    stem: str = Field(min_length=1)
    skill_tag: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MultipleChoiceQuestion(QuestionBase):
    """A multiple-choice question.

    Shape only: 2+ options and a non-empty ``correct_answer``. Whether
    exactly one option matches the answer, whether options are unique,
    and distractor lengths are all checked by the eval harness, not here.
    """

    type: Literal["multiple_choice"] = "multiple_choice"
    options: list[str] = Field(min_length=2)
    correct_answer: str = Field(min_length=1)


class ShortAnswerQuestion(QuestionBase):
    """A short-answer question with a single expected answer.

    Answer-tolerance for grading student responses is out of scope; the
    question just carries the answer. "Stem doesn't contain the answer
    verbatim" is checked by the eval harness, not here.
    """

    type: Literal["short_answer"] = "short_answer"
    answer: str = Field(min_length=1)


# Any question. Pydantic routes a raw dict to the right model by its "type"
# field; a missing or unknown "type" is a single clear validation error.
Question = Annotated[
    MultipleChoiceQuestion | ShortAnswerQuestion,
    Field(discriminator="type"),
]

# A bare union has no .model_validate(); TypeAdapter gives us one.
# Callers parse untrusted data (DB docs, LLM output) via
# QuestionAdapter.validate_python(...).
QuestionAdapter = TypeAdapter(Question)
