"""Pydantic models for assessment items.

Items are a discriminated union of concrete types (added in 2c/2d) that
share the fields defined here on ``ItemBase``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


def _new_id() -> str:
    return uuid.uuid4().hex


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ItemBase(BaseModel):
    """Fields common to every item type.

    ``extra="forbid"`` so unexpected keys (e.g. from LLM output drift)
    raise a validation error instead of being silently ignored.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    stem: str = Field(min_length=1)
    skill_tag: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
