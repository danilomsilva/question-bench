# question-bench

[![CI](https://github.com/danilomsilva/question-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/danilomsilva/question-bench/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An LLM assessment-question generator with a **deterministic** quality-scoring
harness. You ask for questions, an LLM drafts them, and a fixed set of
rules — not another model's opinion — scores each one. Scores are filed
against the prompt version that produced the question, so changing the
generation prompt shows up as a measurable pass-rate delta.

Portfolio project: the focus is Python, document-oriented data modelling,
TDD, and CI. The React frontend is deliberately thin — a client to
exercise the API, not the thing being demonstrated.

## How it works

1. **Generate** — pick a type (`multiple_choice` / `short_answer`) and a
   topic; the app asks Gemini (or a deterministic stub) to draft questions
   and stores them.
2. **Review / edit** — list and open questions, fix wording or answers.
3. **Evaluate** — run the rule harness against a question: a pass/fail per
   rule plus an overall score, stored as an append-only report.
4. **Compare** — pass rate by prompt version, so prompt edits can be
   judged by their effect on quality.

## Stack

| Area | Choice |
|------|--------|
| Language / tooling | Python 3.12, [uv](https://docs.astral.sh/uv/), ruff |
| API | FastAPI + Pydantic v2 |
| DB | MongoDB via `motor` (async) |
| LLM | Gemini (`google-genai`), behind a swappable seam |
| Frontend | Vite + React 19 + TypeScript + Tailwind 4 + TanStack Query |
| Tests / CI | pytest, GitHub Actions (lint + tests + Mongo service + docker smoke + frontend build) |

## Running it

### Whole stack (Docker)

```bash
docker compose up --build          # API on http://localhost:8000
uv run python scripts/seed.py      # optional: example data
```

`GET /health`, interactive docs at `/docs`.

### Local development

```bash
uv sync
docker compose up -d mongo         # or set MONGO_URL / run without Mongo (in-memory store)
uv run uvicorn question_bench.api:app --reload

cd frontend && npm install && npm run dev   # http://localhost:5173, proxies the API
```

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` to use the real
model; otherwise a deterministic stub generator is used.

### Tests

```bash
uv run pytest                      # Mongo-marked tests skip if no MongoDB is reachable
docker compose up -d mongo && uv run pytest   # run everything
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/generate` | Draft and store questions (`question_type`, `topic`, `count` 1–10) |
| `GET` | `/questions` | List, filter by `question_type` / `topic`, `limit` / `offset` |
| `GET` | `/questions/{id}` | One question |
| `PATCH` | `/questions/{id}` | Partial update; re-validated; `id`/`type`/`created_at`/`prompt_version` are immutable |
| `POST` | `/questions/{id}/evaluate` | Run the harness, store and return the report |
| `GET` | `/stats/pass-rate` | Pass rate grouped by `prompt_version` (not in the original brief; added so the deltas have a reader) |

## Eval rules

Deterministic checks, dispatched by question type:

| Rule | Applies to |
|------|-----------|
| exactly one option equals the correct answer | multiple choice |
| no duplicate options | multiple choice |
| each distractor's length within ±30% of the correct answer's | multiple choice |
| the stem does not contain the answer verbatim | both |
| `topic` is in the allowed vocabulary | both |

`score` is the fraction of applicable rules that passed, so multiple
choice (5 rules) and short answer (2) stay comparable on one 0–1 scale.

## Design decisions

- **Discriminated union, single collection.** `multiple_choice` and
  `short_answer` share a base and carry their own fields; a `type`
  discriminator routes parsing. One `questions` collection matches the
  document-store model and keeps `GET /questions` a single query.
- **Models validate shape, not quality.** A model will happily hold a bad
  question — that's required, because you can't score a question you refused to
  store. Every quality judgement lives in the harness. `extra="forbid"`
  so unexpected LLM fields fail loudly.
- **Deterministic rules, not LLM-as-judge.** Reproducible, free to run,
  and the only way pass-rate deltas between prompt versions mean
  anything.
- **`RuleResult` is a plain frozen dataclass; `EvaluationReport` is
  Pydantic.** The report crosses the API/DB boundary; the individual
  results don't.
- **Evaluation history is append-only.** Pass-rate-delta analysis needs
  every run, across prompt versions and re-evaluations — not just the
  latest.
- **`QuestionStore` is a `Protocol`.** The in-memory and MongoDB stores match
  a shape; nothing inherits. Swapping them is one line in the DI wiring
  (`get_store` picks Mongo when a client is connected, in-memory
  otherwise — which is also what keeps the endpoint tests fast).
- **The LLM is behind `QuestionGenerator`.** `GeminiQuestionGenerator` for real
  use, `StubQuestionGenerator` for everything else. Turning raw model JSON
  into validated documents is pure and unit-tested; the HTTP call is not.
- **`motor` for the driver** — chosen despite its May 2025 deprecation in
  favour of PyMongo's native async client. A real project would use
  `pymongo.AsyncMongoClient`.
- **Real MongoDB in tests, not `mongomock`.** Fidelity (aggregation
  pipelines, indexes) over convenience; a container in CI, `skipif`
  locally.
- **`src/` layout.** Tests run against the installed package, so a broken
  packaging config fails a test instead of hiding.

## Project layout

```
src/question_bench/    models · eval harness · store (Protocol + in-memory + Mongo) · llm · api · settings · db
tests/                  unit + TestClient + @pytest.mark.mongo integration tests
frontend/               Vite React SPA (generate / questions / detail+edit / pass-rate)
scripts/seed.py         example data against a running instance
docs/                   implementation plan (build order, decisions, checkboxes)
```

## Out of scope

Auth, deployment, RAG, streaming, multi-user, and question types beyond the
two named.
