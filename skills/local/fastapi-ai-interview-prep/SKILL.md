---
name: fastapi-ai-interview-prep
description: FastAPI + AI engineering interview preparation — 100 self-contained Q&A across 10 topics (ASGI, Pydantic, REST, dependency injection, databases, security, testing, async, AI/ML/RAG/LLM serving, deployment) plus a quiz CLI. Use when preparing for a FastAPI/Python backend or AI-engineer interview, running or being given a mock interview, drilling a specific topic, or self-testing against senior-level answer rubrics.
---

# FastAPI AI Interview Prep

A question bank and mock-interviewer toolkit for FastAPI + AI-engineering roles.
Ten topic files hold ten questions each (100 total), every one with a model answer
that includes the **senior signal** an interviewer listens for — the distinction
that separates "knows the API" from "has run this in production."

> Inspired by the topic coverage of *FastAPI for AI Engineers* (AI Engineering
> Insider, 2026). All questions and answers here are written from scratch; this is
> not a reproduction of the book's question set.

## When to use

- "Help me prep for a FastAPI / Python backend / AI-engineer interview"
- "Give me a mock interview" / "quiz me on FastAPI" / "ask me async questions"
- Drilling one weak area (e.g. RAG serving, JWT security, testing strategy)
- Self-testing: answer first, then check against the rubric

## When NOT to use

- You want to *understand* a pattern to apply it now → use `fastapi-ai-patterns`
- You want to *build* a service → use `fastapi-ai-scaffold`

## How to run a session

### Mode A — Mock interview (you are the interviewer)

1. Draw questions without answers (so you can react to the candidate live):

```bash
python3 scripts/quiz.py --random 5
```

2. Ask one at a time. Let the candidate answer before revealing anything.
3. Reveal the rubric for that id only when scoring:

```bash
python3 scripts/quiz.py --answer ch09-q4
```

4. Grade against the **senior signal**, not keyword bingo (see rubric below).

### Mode B — Topic drill

```bash
python3 scripts/quiz.py --topics                       # list chapters + counts
python3 scripts/quiz.py --topic ch08 --random 4        # async, questions only
python3 scripts/quiz.py --topic ch08 --list --with-answers   # study a whole topic
```

### Mode C — Self-test

```bash
python3 scripts/quiz.py --random 3            # answer out loud / in writing first
python3 scripts/quiz.py --random 3 --seed 42 --with-answers   # same draw, with rubrics
```

## Grading rubric (how to score an answer)

For each question, weight the answer on:

1. **Correctness** — the core mechanism is right.
2. **Senior signal** — names the production consequence, trade-off, or failure mode,
   not just the definition (e.g. for `def` vs `async def`, mentions that a blocking
   call in `async def` stalls the whole loop and degrades *unrelated* endpoints).
3. **Scenario handling** — for the "you observe X, diagnose it" questions, looks for a
   *method* (decompose, measure, isolate) rather than a single guessed cause.

A junior answer defines the term; a senior answer says what breaks in production and
what they'd do about it. The model answers are written to that bar.

## Topic map (reference files)

Each file is self-contained; load the one matching the area you're drilling.

| File | Chapter scope |
|---|---|
| `references/ch01-intro.md` | FastAPI/ASGI/REST/OpenAPI fundamentals |
| `references/ch02-pydantic.md` | Typing, Pydantic v2, validation, schema design |
| `references/ch03-endpoints.md` | Verbs, status codes, pagination, versioning |
| `references/ch04-dependency-injection.md` | `Depends()`, layering, project structure |
| `references/ch05-database.md` | SQLAlchemy/SQLModel, N+1, pooling, Alembic |
| `references/ch06-security.md` | Auth, JWT, OWASP API risks, BOLA |
| `references/ch07-testing.md` | TestClient, overrides, test DB strategy, coverage |
| `references/ch08-async.md` | Event loop, retries, queues, webhooks, streaming |
| `references/ch09-ai-serving.md` | ML/RAG/LLM serving — the core of the role |
| `references/ch10-deployment.md` | Probes, scaling, observability, degradation |

## Available scripts

- **`scripts/quiz.py`** — Draw/list/reveal questions parsed from the references.
  - Flags: `--list`, `--topics`, `--count`, `--random N`, `--topic chNN`,
    `--answer ID`, `--with-answers`, `--seed N`, `--json`, `--help`.
  - Stdlib only; run with `python3` or `uv run`.

## Gotchas

- **Don't reveal answers before the candidate responds.** Use `--random` (no
  `--with-answers`) to ask, and `--answer <id>` only when scoring — otherwise the
  exercise tests reading, not recall.
- **Answers are written rubrics, not scripts to recite.** Score for the senior signal
  and the diagnostic method; a differently-worded answer that names the production
  consequence is a pass.
- **`quiz.py` parses the reference markdown live.** If you add questions, keep the
  exact `### Q<n>. <text>` heading format or they won't be picked up (the parser
  ends an answer at the next markdown heading).
- **These mirror the book's topics, not its wording.** Treat them as equivalent
  practice; the real interview will phrase things differently, which is the point.
