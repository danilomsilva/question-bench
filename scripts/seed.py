"""Populate a running question-bench instance with example data.

    uv run python scripts/seed.py                     # http://localhost:8000
    API_BASE=http://host:8000 uv run python scripts/seed.py

Generates a handful of questions across topics and evaluates each, so the
Questions and Pass-rate views have something to show.
"""

from __future__ import annotations
import os
import sys
import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

PLAN = [
    ("multiple_choice", "arithmetic", 3),
    ("multiple_choice", "fractions", 2),
    ("short_answer", "algebra", 2),
]


def main() -> int:
    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        client.get("/health").raise_for_status()

        created: list[dict] = []
        for question_type, topic, count in PLAN:
            response = client.post(
                "/generate",
                json={
                    "question_type": question_type,
                    "topic": topic,
                    "count": count,
                },
            )
            response.raise_for_status()
            created.extend(response.json())

        for question in created:
            client.post(f"/questions/{question['id']}/evaluate").raise_for_status()

    print(f"seeded {len(created)} questions and evaluated each")
    return 0


if __name__ == "__main__":
    sys.exit(main())
