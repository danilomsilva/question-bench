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
- [ ] 1.5a `.github/workflows/ci.yml` — `uv sync --locked`, `ruff check`, `ruff format --check`, `pytest` on ubuntu-latest
- [ ] 1.5b Confirm first run is green on GitHub
- Grow later: Mongo service container (Step 5), maybe an OS matrix, maybe a coverage gate

## Step 2 — Item data model
- [x] 2a **(decision)** Collection strategy → **discriminated union (shared base + per-type models) + single `items` collection**
- [ ] 2b Shared base fields — `id`, `type`, `skill_tag`, `prompt_version`, timestamps, `status`
- [ ] 2c `multiple_choice` model — stem, options, correct-answer representation
- [ ] 2d `short_answer` model — stem, accepted answer(s)
- [ ] 2e Discriminated union + parsing (Pydantic `Field(discriminator=...)`)
- [ ] 2f Allowed `skill_tag` list — where the constant lives
- [ ] 2g Example instances / fixtures for tests
- [ ] 2h Verify: models validate good input, reject bad input

## Step 3 — Eval rules (tests first)
- [ ] 3a Test fixtures — a valid item plus one deliberately-broken item per rule
- [ ] 3b Rule: exactly one correct answer — test, then implement
- [ ] 3c Rule: no duplicate options — test, then implement
- [ ] 3d Rule: distractors within ±30% length of correct answer — test, then implement
- [ ] 3e Rule: stem does not contain the answer verbatim — test, then implement
- [ ] 3f Rule: `skill_tag` present and in allowed list — test, then implement
- [ ] 3g Result model — per-rule pass/fail + detail, overall score
- [ ] 3h Aggregator — run all rules over an item, return the result model — test, then implement
- [ ] 3i **(decision)** Score persistence shape — how a score is stored against `prompt_version`
- [ ] 3j Verify: full suite green, predict-then-run confirmed

## Step 4 — FastAPI app + endpoints
- [ ] 4a App skeleton + settings (`pydantic-settings`, env var for the Gemini key)
- [ ] 4b **(decision)** Store interface (Protocol/ABC) + in-memory implementation
- [ ] 4c `POST /generate` — request model, Gemini client (stubbed first), map response to item model, persist
- [ ] 4d `GET /items` — list; **(decision)** filtering + pagination
- [ ] 4e `GET /items/{id}`
- [ ] 4f `PATCH /items/{id}` — partial-update semantics, re-validation
- [ ] 4g `POST /items/{id}/evaluate` — run the harness, persist the score
- [ ] 4h Error handling + response models — 404, 422, Gemini failure
- [ ] 4i Dependency injection (`Depends`) for store + services
- [ ] 4j Verify: endpoint tests via `TestClient`, all green

## Step 5 — MongoDB integration
- [ ] 5a **(decision)** Driver — `motor` (async) vs `pymongo`
- [ ] 5b Connection lifecycle — `lifespan` startup/shutdown
- [ ] 5c Mongo-backed implementation of the store interface
- [ ] 5d Document (de)serialisation — Pydantic ↔ BSON, `_id` handling
- [ ] 5e Indexes — `skill_tag`, `prompt_version`, `type`, `created_at`
- [ ] 5f **(decision)** Test strategy — `mongomock` vs testcontainers vs ephemeral service
- [ ] 5g Verify: store tests pass against real Mongo, endpoint tests still green

## Step 6 — Infra
- [ ] 6a `Dockerfile` — multi-stage
- [ ] 6b `.dockerignore`
- [ ] 6c `docker-compose.yml` — app + mongo, volumes, env
- [ ] 6d Extend CI (from Step 1.5) — add Mongo service container
- [ ] 6e Verify: `docker compose up` runs the app end to end; CI green on a pushed branch

## Step 7 — Frontend (build-without-asking)
- [ ] 7a Vite + React + TS + Tailwind scaffold
- [ ] 7b API client + TanStack Query setup
- [ ] 7c Generate screen — form (type, `skill_tag`, count)
- [ ] 7d Items list screen
- [ ] 7e Item detail + edit screen
- [ ] 7f Evaluate action + results display
- [ ] 7g `prompt_version` pass-rate view

## Step 8 — Wrap-up
- [ ] 8a `README.md` — what it is, how to run, design decisions & trade-offs (interview defence)
- [ ] 8b Seed script / example data
- [ ] 8c Final pass — `ruff` clean, full test suite green, `compose up` works end to end
