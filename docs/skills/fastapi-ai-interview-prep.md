# fastapi-ai-interview-prep

A question bank and mock-interviewer toolkit for FastAPI + AI-engineering roles.
Ten topic files hold ten questions each (100 total), every answer written to the
**senior signal** an interviewer listens for — the production consequence or
trade-off that separates "knows the API" from "has run this at scale."

> Inspired by the topic coverage of *FastAPI for AI Engineers* (AI Engineering
> Insider, 2026). All questions and answers are written from scratch; this is not a
> reproduction of the book's question set.

## What ships

- The full SKILL.md
  ([skills/local/fastapi-ai-interview-prep/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/SKILL.md))
  — three session modes (mock interview, topic drill, self-test) and a grading
  rubric (correctness → senior signal → scenario method).
- Ten reference files (`references/ch01-intro.md` … `ch10-deployment.md`), one per
  chapter, 10 self-written Q&A each:
  [intro/ASGI](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch01-intro.md),
  [Pydantic](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch02-pydantic.md),
  [endpoints](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch03-endpoints.md),
  [dependency injection](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch04-dependency-injection.md),
  [databases](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch05-database.md),
  [security](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch06-security.md),
  [testing](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch07-testing.md),
  [async](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch08-async.md),
  [AI serving](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch09-ai-serving.md),
  [deployment](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/references/ch10-deployment.md).
- One script:
    - [`quiz.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-interview-prep/scripts/quiz.py)
      — draws/lists/reveals questions parsed live from the references. Stdlib only.

## Quick start

```bash
cd skills/local/fastapi-ai-interview-prep

python3 scripts/quiz.py --topics              # chapters + counts
python3 scripts/quiz.py --random 5            # ask 5 (no answers)
python3 scripts/quiz.py --answer ch09-q4      # reveal one rubric
python3 scripts/quiz.py --topic ch08 --random 4 --with-answers
python3 scripts/quiz.py --random 3 --seed 42 --json   # reproducible, machine-readable
```

Run a mock interview by drawing questions without answers, letting the candidate
respond, then revealing the rubric per id to score against the senior signal.

## Cross-references

- To *apply* these patterns: [`fastapi-ai-patterns`](fastapi-ai-patterns.md).
- To *build* a service: [`fastapi-ai-scaffold`](fastapi-ai-scaffold.md).
