"""Item generation.

``ItemGenerator`` is the seam for the LLM. The real Gemini client will
implement the same call; ``StubItemGenerator`` fabricates deterministic,
rule-passing items so the rest of the system can be built and tested
without a network or an API key.
"""

from __future__ import annotations

from typing import Protocol

from item_bench.models import Item, MultipleChoiceItem, ShortAnswerItem


class GenerationError(RuntimeError):
    """Raised when the underlying generator fails (network, quota, bad output)."""


class ItemGenerator(Protocol):
    def generate(
        self, *, item_type: str, skill_tag: str, count: int, prompt_version: str
    ) -> list[Item]: ...


class StubItemGenerator:
    """Deterministic fake generator. No LLM, no randomness."""

    def generate(
        self, *, item_type: str, skill_tag: str, count: int, prompt_version: str
    ) -> list[Item]:
        if item_type == "multiple_choice":
            return [
                MultipleChoiceItem(
                    stem=f"Sample multiple-choice question about {skill_tag} (#{i})",
                    skill_tag=skill_tag,
                    prompt_version=prompt_version,
                    # All options length 5 so the distractor-length rule passes.
                    options=["alpha", "bravo", "delta", "gamma"],
                    correct_answer="alpha",
                )
                for i in range(count)
            ]
        return [
            ShortAnswerItem(
                stem=f"Sample short-answer question about {skill_tag} (#{i})",
                skill_tag=skill_tag,
                prompt_version=prompt_version,
                answer=f"response-{i}",
            )
            for i in range(count)
        ]
