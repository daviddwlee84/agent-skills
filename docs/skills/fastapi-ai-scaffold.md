# fastapi-ai-scaffold

Generates a runnable, production-shaped FastAPI AI/ML service from a bundled
skeleton, so you don't re-derive the same wiring every time. The generated tree
encodes the patterns from [`fastapi-ai-patterns`](fastapi-ai-patterns.md) as
working code — the boring-but-correct baseline an inference service needs before it
sees traffic.

> Inspired by *FastAPI for AI Engineers* (AI Engineering Insider, 2026). All
> generated code is original.

## What ships

- The full SKILL.md
  ([skills/local/fastapi-ai-scaffold/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-scaffold/SKILL.md))
  — when to use, what's generated, and how to replace the stubs with your model.
- One script:
    - [`new-fastapi-ai-service.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh)
      — copies the skeleton, strips each file's `.tmpl` suffix, substitutes the
      project slug. Bash 3.2; `--help` / `--dry-run` / `--name` / `--force`; JSON
      summary on stdout.
- A 44-file skeleton under
  [`assets/project/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/fastapi-ai-scaffold/assets/project)
  (every file `*.tmpl`): clean-architecture `app/` (router → service →
  repository), `lifespan`-loaded model + shared `httpx.AsyncClient` + DB engine,
  `/health` + `/ready` probes, JWT auth (pinned algorithm, bcrypt), SQLModel +
  Alembic, an SSE LLM gateway, guardrails + a Pydantic validation loop, structured
  JSON logging, `tests/` using `dependency_overrides` + in-memory SQLite, plus
  `Dockerfile`, `gunicorn_conf.py`, `pyproject.toml`, and `.env.example`.

## Quick start

```bash
# Preview, write nothing:
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh --dry-run ./my-service

# Generate:
bash skills/local/fastapi-ai-scaffold/scripts/new-fastapi-ai-service.sh ./my-service

cd ./my-service
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env          # set JWT_SECRET, DATABASE_URL, MODEL_PATH
uvicorn app.main:app --reload # http://127.0.0.1:8000/docs
pytest -q                     # bundled tests pass immediately
```

The bundled tests and a real-lifespan boot are verified before shipping, so a
freshly generated project runs green out of the box.

## Notes

- The generated package is always `app`; only project *metadata* (pyproject name,
  README title, `.env` `APP_NAME`) uses the slug.
- The model + LLM in `app/ml/model.py` are deterministic stubs — replace them with
  your real artifact; the structure and offloading stay.

## Cross-references

- Pattern rationale for every generated piece: [`fastapi-ai-patterns`](fastapi-ai-patterns.md).
- FastAPI docs: [fastapi.tiangolo.com](https://fastapi.tiangolo.com).
