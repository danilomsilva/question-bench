"""Runtime configuration, read from the environment (or a local .env).

Kept tiny on purpose: only what the app needs to boot and to stamp
generated questions with a prompt version.
"""

from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Empty by default so the app (and the test suite) boot without a key;
    # the real Gemini client requires it, the stub generator doesn't.
    gemini_api_key: str = ""

    # Stamped onto every generated question so eval scores can be grouped by
    # the prompt that produced them.
    prompt_version: str = "stub-v1"

    # When the app boots with a reachable Mongo it uses MongoQuestionStore;
    # otherwise (and in unit tests) it falls back to the in-memory store.
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "question_bench"


@lru_cache
def get_settings() -> Settings:
    return Settings()
