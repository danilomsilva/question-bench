"""Pydantic models for assessment items.

Items are a discriminated union of concrete types (added in 2c/2d) that
share the fields defined here on ``ItemBase``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Fields common to every item type.

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


class MultipleChoiceItem(ItemBase):
    """A multiple-choice question.

    Shape only: 2+ options and a non-empty ``correct_answer``. Whether
    exactly one option matches the answer, whether options are unique,
    and distractor lengths are all checked by the eval harness, not here.
    """

    type: Literal["multiple_choice"] = "multiple_choice"
    options: list[str] = Field(min_length=2)
    correct_answer: str = Field(min_length=1)
