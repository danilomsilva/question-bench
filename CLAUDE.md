# item-bench

LLM assessment-item generator with a deterministic quality-scoring harness.
Portfolio project for Senior Software Engineer interviews.

## Purpose
Demonstrate Python, document-oriented data modelling, TDD, and CI —
NOT frontend skill (already established elsewhere).

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
