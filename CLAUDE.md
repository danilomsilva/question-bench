# item-bench

LLM assessment-item generator with a deterministic quality-scoring harness.
Portfolio project for Senior Software Engineer interviews.

## Purpose
Demonstrate Python, document-oriented data modelling, TDD, and CI —
NOT frontend skill (already established elsewhere).

## How it works (plain-language walkthrough)

The app helps a teacher or content author create test questions quickly,
then checks their quality automatically instead of by eye.

1. **Ask for questions.** The user picks a question type (multiple choice
   or short answer) and a skill tag (e.g. "fractions"), and requests a
   batch. The app asks an LLM (Gemini) to draft them.
   *`POST /generate` — request validated by Pydantic, questions drafted by
   Gemini (Google AI Studio API), stored as documents in MongoDB.*
2. **Review the drafts.** The generated questions appear in a list. The
   user opens any one to see the full question text, the answer options,
   and which option is marked correct.
   *`GET /items`, `GET /items/{id}` — React list and detail views, data
   fetched and cached with TanStack Query.*
3. **Edit if needed.** The user can fix wording, swap an option, or
   change the correct answer directly in the app.
   *`PATCH /items/{id}` — partial update, re-validated by Pydantic.*
4. **Run the quality check.** One click runs a fixed set of rules against
   the question — not a second AI opinion, but concrete checks like
   "exactly one correct answer" and "no repeated options". The result is
   a pass/fail for each rule plus an overall score.
   *`POST /items/{id}/evaluate` — deterministic rule harness in plain
   Python, covered by pytest; returns per-rule pass/fail and a score.*
5. **See whether the prompt is improving.** Every score is filed under the
   prompt version that produced it, so changing the generation prompt
   shows up as a measurable rise or fall in pass rate.
   *Scores persisted in MongoDB keyed by `prompt_version`; pass-rate
   deltas surfaced in the UI.*

What the user never has to do: write questions from scratch, or manually
re-check every draft for the same recurring mistakes.

## Stack
- Backend: Python 3.12, FastAPI, Pydantic
- DB: MongoDB (document store; items have heterogeneous shapes per type)
- LLM: Gemini via Google AI Studio API
- Frontend: React + TypeScript + Tailwind + TanStack Query
- Tests: pytest. CI: GitHub Actions (ruff + pytest). Docker + compose.

## Scope
Two item types only: multiple_choice, short_answer.
Endpoints: POST /generate, GET /items, GET /items/{id},
PATCH /items/{id}, POST /items/{id}/evaluate

## Eval rules (deterministic, not LLM-as-judge)
- exactly one correct answer
- no duplicate options
- distractors within ±30% length of correct answer
- stem does not contain the answer verbatim
- skill_tag present and in allowed list
Scores stored against prompt_version so prompt changes show as pass-rate deltas.

## Out of scope
Auth, deployment, RAG, streaming, multi-user, extra item types.

## Working rules
- Write eval-rule tests BEFORE the implementation.
- Explain trade-offs as we go; I need to defend these decisions verbally.
- Keep commits small and frequent.

## Pace and collaboration

Primary purpose is my learning, not delivery speed.
I am a senior TypeScript/React engineer. Python, MongoDB, and authoring
infra config are new to me. I have to defend every decision in this repo
verbally in an interview.

### 1. Default loop — for every unit of work
1. State what we're about to build and why it comes now.
2. Explain the approach BEFORE writing code. Use plan mode.
3. Where a TS/Node equivalent exists, explain via that analogy — then
   say where the analogy breaks down.
4. If there's a real trade-off, give me the options and let ME choose.
   Don't pick for me and don't hide the alternative.
5. WAIT for my approval.
6. Write a small diff. Never more than ~50 lines without checking in.
7. Ask me to predict the outcome before running tests.
8. Stop. Summarise what changed in two lines. Wait for me.

### 2. Explain-then-build applies to
- Anything Python-idiomatic (typing, Pydantic, async, comprehensions,
  decorators, dependency injection)
- MongoDB schema design and queries
- Eval harness logic
- API design decisions
- Dockerfile, docker-compose, GitHub Actions

For infra specifically: build up, don't hand me a finished file.
Start with the smallest thing that works, explain each directive line
by line, then tell me what's wrong with it and let me decide what to fix.
Never paste a complete config and summarise it afterwards.

### 3. Build-without-asking
React components, Tailwind config, TanStack Query wiring.
Write it, one line on what it does, move on.

### 4. Standing rules
- One concept at a time.
- Tests before implementation for the eval rules.
- Small, frequent commits with meaningful messages.
- If I approve something I clearly haven't understood, say so and
  re-explain rather than proceeding.
- Don't optimise ahead of need. If you're adding something for
  robustness I didn't ask for, flag it as optional first.
