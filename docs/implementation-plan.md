# Implementation plan

Single source of truth for build order and progress. Work top to bottom.
Don't start the next item until the current one is done, its box is
ticked, and the change is pushed. Items marked **(decision)** are real
trade-offs — stop and choose before building.

Legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Step 0 — Project setup docs
- [x] `CLAUDE.md` — project brief, scope, collaboration rules
- [x] `docs/implementation-plan.md` — this file

## Step 1 — Repo skeleton + tooling
- [x] 1a **(decision)** Dependency manager: `uv` / Poetry / `pip`+`venv` → **uv**
- [x] 1b Folder layout (`src/` layout vs flat, where tests live) → **src/ layout** via `uv init --lib`
- [x] 1c `pyproject.toml` — project metadata, where dependencies are declared
- [x] 1f `.gitignore` — pulled ahead of 1d/1e: a `.pyc` slipped into a commit, needed the ignore rules in place first
- [x] 1d `ruff` config — lint + format rules (`E F I UP B SIM`, line-length 88)
- [x] 1e `pytest` config — `testpaths=tests`, `--import-mode=importlib`, strict markers/config, `xfail_strict`
- [x] 1g Verify: `uv sync` + `ruff check` + `ruff format --check` + `pytest` all clean

## Step 1.5 — CI (minimal now, grow later)
Pulled forward from Step 6d so the pipeline is green from the start.
- [x] 1.5a `.github/workflows/ci.yml` — `uv sync --locked`, `ruff check`, `ruff format --check`, `pytest` on ubuntu-latest
- [x] 1.5b Confirm first run is green on GitHub — green in ~12s
- Grow later: Mongo service container (Step 5), maybe an OS matrix, maybe a coverage gate

## Step 2 — Item data model
- [x] 2a **(decision)** Collection strategy → **discriminated union (shared base + per-type models) + single `items` collection**
- [x] 2b Shared base fields — `ItemBase`: uuid4 `id`, `stem`, `skill_tag`, `prompt_version`, `created_at`/`updated_at`, `extra="forbid"` (`status` deferred to Step 4)
- [x] 2c `multiple_choice` model — `MultipleChoiceItem`: `options: list[str]` (2+) + `correct_answer` (flat, not option objects); shape-only validation
- [x] 2d `short_answer` model — `ShortAnswerItem`: single `answer: str` (grading tolerance is out of scope)
- [x] 2e Discriminated union + parsing — `Item = Annotated[MC | SA, Field(discriminator="type")]`, `ItemAdapter = TypeAdapter(Item)`
- [x] 2f Allowed `skill_tag` list — `ALLOWED_SKILL_TAGS` frozenset in `src/item_bench/skill_tags.py` (plain constant, model does NOT enforce membership — that's eval rule 3f)
- [x] 2g Example instances / fixtures for tests — `valid_mc` / `valid_sa` pytest fixtures in `tests/conftest.py`
- [x] 2h Verify: 17 tests green (shape validation + adapter routing + serialise/parse round-trip), ruff clean

## Step 3 — Eval rules (tests first)
- [x] 3a Test-data convention — keep only `valid_mc`/`valid_sa`; each rule test builds its broken item inline via `.model_copy(update=...)`. Rule tests in `tests/test_eval_rules.py`, harness code in `src/item_bench/eval.py`
- [x] 3g Result value object — `RuleResult(rule, passed, detail)`, frozen dataclass (pulled ahead of the rules so each rule has a consistent return type)
- [x] 3b Rule: `exactly_one_correct_answer` (MC) — exactly one option equals `correct_answer`
- [x] 3c Rule: `no_duplicate_options` (MC) — every option string distinct
- [x] 3d Rule: `distractor_length_within_30pct` (MC) — each distractor's length within 0.7–1.3× the correct answer's
- [x] 3e Rule: `stem_excludes_answer` (MC + SA) — answer not a verbatim (case-sensitive) substring of the stem
- [x] 3f Rule: `skill_tag_allowed` (MC + SA) — `skill_tag` in `ALLOWED_SKILL_TAGS`
- [x] 3h Aggregator — `evaluate(item) -> EvaluationReport`: runs the rules for the item's type (MC: 5, SA: 2), `score` = passed/total, `passed` = all passed
- [x] 3i **(decision)** Score persistence shape — store one `EvaluationReport` document per evaluation, append-only (not overwrite), queried by `prompt_version` / `item_id` / `evaluated_at`. Rationale: pass-rate-delta analysis needs history across prompt versions and re-runs. Actual Mongo write lands in Step 5 — **flag if you disagree before then.**
- [x] 3j Verify: 35 tests green (rules + aggregator + serialisation), ruff clean

## Step 4 — FastAPI app + endpoints
- [x] 4a App skeleton + `Settings` (`pydantic-settings`; `gemini_api_key` optional, `prompt_version` default `stub-v1`) + `GET /health`
- [x] 4b **(decision)** `ItemStore` **Protocol** (structural, nothing inherits) + `InMemoryItemStore` (dict-backed, also holds `EvaluationReport`s)
- [x] 4c `POST /generate` — `GenerateRequest` (type, skill_tag, count 1–10), `StubItemGenerator` behind an `ItemGenerator` Protocol produces rule-passing items, persisted, 201
- [x] 4d `GET /items` — **(decision)** filters `item_type` + `skill_tag`, offset/limit pagination (limit 1–200 default 50); cursor pagination noted as overkill at this scope
- [x] 4e `GET /items/{id}` — 404 when missing
- [x] 4f `PATCH /items/{id}` — JSON body; protected fields (`id`/`type`/`created_at`/`prompt_version`) → 422; merge → re-parse through `ItemAdapter` (full re-validation) → bump `updated_at`
- [x] 4g `POST /items/{id}/evaluate` — runs `evaluate()`, stores the `EvaluationReport`, returns it
- [x] 4h Errors + `response_model` — 404 (missing), 422 (bad body / protected / shape), 502 (`GenerationError`)
- [x] 4i DI via `Depends` — `get_store` / `get_generator` / `get_settings`; tests swap the store with `app.dependency_overrides`
- [x] 4j Verify: 49 tests green (14 `TestClient` endpoint tests), ruff clean

## Step 5 — MongoDB integration
- [x] 5a **(decision)** Driver — **motor** (async). Note: motor was deprecated May 2025 in favour of PyMongo's native `AsyncMongoClient`; chosen anyway. Store + routes go async as a result.
- [x] 5b Connection lifecycle — `db.lifespan` builds/closes the motor client (lazy connect); `ItemStore` Protocol + `InMemoryItemStore` + all routes are now `async`; `get_store` returns Mongo when `app.state.mongo_db` is set, else in-memory
- [x] 5c Mongo-backed store — `MongoItemStore` (collections `items`, `evaluations`), all `ItemStore` methods; list sorted by `created_at` for parity with the in-memory store
- [x] 5d (De)serialisation — `model_dump(mode="python")` keeps `datetime` for BSON; item uuid is the `_id` (no second id); reads re-parse through `ItemAdapter`; client is `tz_aware`; round-trip tests allow sub-ms drift (BSON is ms precision). *Landed with 5c — the store can't exist without its serialisation.*
- [x] 5e Indexes — `db.ensure_indexes()` (idempotent, run from `lifespan`): `items` on `type`/`skill_tag`/`prompt_version`/`created_at`, `evaluations` on `item_id`/`prompt_version`/`evaluated_at`
- [x] 5f **(decision)** Test strategy — **real MongoDB, not a fake.** Local: `compose.yaml` (`docker compose up -d mongo`). CI: GitHub Actions `services:` container. Tests read `MONGO_URL` and `skipif` it's unreachable. This is the common Python-web-shop approach and reuses the Step 6 compose file; `mongomock` rejected on fidelity, testcontainers rejected as an extra dependency.
- [x] 5g Verify: 8 `@pytest.mark.mongo` tests run against real MongoDB in CI (skip locally without Docker); 49 non-mongo tests still green

## Step 6 — Infra
- [x] 6a `Dockerfile` — 2-stage (uv builder → slim runtime), deps cached as their own layer, non-root user, `uvicorn` CMD
- [x] 6b `.dockerignore` — keeps `README.md` (build backend needs it), drops `.venv`/`tests`/`docs`/caches/env
- [x] 6c `compose.yaml` — `app` (built here) + `mongo` (healthcheck + `depends_on: service_healthy`); `MONGO_URL=mongodb://mongo:27017`
- [x] 6d CI Mongo service — added back in 5f; `uvicorn[standard]` added as a runtime dep here
- [x] 6e Verify: new `docker-smoke` CI job runs `docker compose up --build`, waits on `/health`, then `POST /generate` + `GET /items` to prove the container talks to Mongo end to end

## Step 7 — Frontend (build-without-asking), kept in this repo under `frontend/`
- [x] 7a Vite 6 + React 19 + TS + Tailwind 4 scaffold; dev proxy to `:8000`; `frontend` CI job (`npm ci` + `npm run build`, which also typechecks)
- [x] 7b `src/api.ts` — hand-written types mirroring the Pydantic models + typed `fetch` wrappers for all five endpoints; `QueryClientProvider` wired in `main.tsx`
- [x] 7c `GenerateView` — form (type / skill_tag / count), `useMutation` on POST /generate, invalidates the items query on success
- [x] 7d `ItemsView` — `useQuery` on `GET /items` keyed by filters, `item_type`/`skill_tag` filter controls, table with row-click to select
- [x] 7e `ItemDetailView` — read-only meta + edit form (`stem`, plus `options`/`correct_answer` or `answer`), `PATCH /items/{id}` via `useMutation`, invalidates item + list queries
- [x] 7f `EvaluateSection` in the detail view — `POST /items/{id}/evaluate`, shows overall PASS/FAIL + score and a per-rule ✓/✗ list with failure detail
- [x] 7g `PassRateView` + new `GET /stats/pass-rate` endpoint — aggregates the `evaluations` collection by `prompt_version` (Mongo `$group` pipeline; in-memory groups in Python). Not in the brief's five endpoints, but "pass-rate deltas" had no reader; kept read-only.

## Step 8 — Wrap-up
- [x] 8d Real Gemini generator — `GeminiItemGenerator` (`google-genai`), used when `GEMINI_API_KEY` is set, stub otherwise. The interesting part — raw LLM JSON → validated documents via the models — is pure and unit-tested; the HTTP call is not (no key in CI).
- [x] 8a `README.md` — what/how-to-run/API/eval rules/design decisions
- [x] 8b `scripts/seed.py` — hits a running instance to generate items across skill tags and evaluate each
- [x] 8c Final pass — ruff clean, 60 tests green in CI (55 + 5 mongo), frontend build green, docker-smoke green, `setup-node` bumped to v5 (Node 20 annotation gone)
