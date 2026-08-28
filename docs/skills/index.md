# Skills overview

This page indexes the skills bundled in this repo.

- **Local skills** (`skills/local/`) are authored and maintained here.
- **Vendored skills** (`skills/vendor/`) are cherry-picked from upstream
  repos and synced via the
  [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
  manifest — see [Adding vendor skills](../workflows/adding-vendor-skills.md).
  Do not edit vendored SKILL.md files locally; changes will be clobbered
  on the next `make sync`.

## Local skills

Custom-authored, curated to this repo's conventions (see
[Conventions](../conventions.md)).

| Skill | One-line | Detailed page |
|---|---|---|
| [`project-knowledge-harness`](project-knowledge-harness.md) | TODO + backlog + pitfalls structure with a bundled validator/init/promote toolkit | [docs](project-knowledge-harness.md) |
| [`quantatitive-factor-researcher`](quantatitive-factor-researcher.md) | Quantitative factor research persona for Python-based strategy work | [docs](quantatitive-factor-researcher.md) |
| [`skill-author`](skill-author.md) | Author new skills following agentskills.io best practices; ships `new-skill.sh` and `lint-skill.sh` | [docs](skill-author.md) |
| [`verifiable-surfaces`](verifiable-surfaces.md) | Design verifiable CLI/tool/service surfaces (`--help`/`--dry-run`/`--print-config`/isolated smoke) and verify config changes via app-native loaders | [docs](verifiable-surfaces.md) |
| [`12-factor-agent-design-review`](12-factor-agent-design-review.md) | Design or evidence-review production LLM applications across prompts, context, typed tools, durable state, owned control flow, pause/resume, humans, retries, and replay | [docs](12-factor-agent-design-review.md) |
| [`demo-evidence`](demo-evidence.md) | Capture acceptance evidence (screenshots/recordings/HTTP logs) into a gitignored `.evidence/` bundle keyed to git branch/commit + agent session, for async "Demos over diffs" review | [docs](demo-evidence.md) |
| [`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.md) | Bootstrap a MkDocs Material site + GitHub Pages deploy; consent-gated with `.skills/preferences.yaml` | [docs](mkdocs-site-bootstrap.md) |
| [`marimo-batch-mlflow`](marimo-batch-mlflow.md) | marimo dual-mode (UI + batch CLI) notebooks with Tyro + MLflow | [docs](marimo-batch-mlflow.md) |
| [`dvc-ml-workflow`](dvc-ml-workflow.md) | DVC pipelines + queued experiments with metrics auto-bound to ephemeral commits; ships init/queue/lint helpers | [docs](dvc-ml-workflow.md) |
| [`mlflow-tracking`](mlflow-tracking.md) | Generic MLflow skill — sqlite + `mlflow ui`, vendored PostgreSQL + MinIO docker stack, LLM tracing, registry, autolog | [docs](mlflow-tracking.md) |
| [`agent-history-hygiene`](agent-history-hygiene.md) | Commit transcripts/plans with feature diffs, derive staged harness/model provenance, bootstrap secret scanning, and apply rotate-first leak remediation | [docs](agent-history-hygiene.md) |
| [`git-workflow`](git-workflow.md) | Scale-aware Git workflow with English Conventional Commits, cross-harness AI provenance, linear history, worktrees, SemVer, and commit validation | [docs](git-workflow.md) |
| [`pueue-job-queue`](pueue-job-queue.md) | Drive Nukesor/pueue for queued/parallel/scheduled shell jobs; submit-one + DAG submitter + JSON-summary waiter; observed pueue 4.0.2 schema | [docs](pueue-job-queue.md) |
| [`slurm-hpc`](slurm-hpc.md) | Portable Slurm know-how — sbatch skeleton, resource requests, job chaining (`--dependency=afterok` + the DependencyNeverSatisfied trap), and what actually fences GPU VRAM (shard vs MPS vs MIG) | [docs](slurm-hpc.md) |
| [`long-running-jobs`](long-running-jobs.md) | How an agent should wait for work outlasting a turn — scheduler-owned chaining, one blocking backgrounded wait, filtered event streams, scheduled check-ins last; durable exit-code markers via `run-and-mark.sh` + `check-runs.sh` | [docs](long-running-jobs.md) |
| [`experiment-knowledge-harness`](experiment-knowledge-harness.md) | Research memory for ML/Quant — LEDGER of overturnable findings, payoff-triaged ROADMAP, pre-registered REPORTs with single-axis ablation contract, auto-rendered Mermaid map | [docs](experiment-knowledge-harness.md) |
| [`clash-proxy-api`](clash-proxy-api.md) | Discover & drive a Clash/mihomo external-controller: status/mode/TUN/switch/reload/connections + OS system-proxy toggle; multi-client (Verge Rev, ClashX, mihomo CLI) with enable-the-API guidance | [docs](clash-proxy-api.md) |
| [`fastapi-ai-patterns`](fastapi-ai-patterns.md) | Production FastAPI patterns + gotchas for AI/ML/LLM serving; `def`/`async` decision table + 8 references over all 10 chapters | [docs](fastapi-ai-patterns.md) |
| [`fastapi-ai-scaffold`](fastapi-ai-scaffold.md) | Generate a production-shaped FastAPI AI service (clean architecture, lifespan model, JWT, SSE, probes, tests, Docker); `new-fastapi-ai-service.sh` + 44-file skeleton | [docs](fastapi-ai-scaffold.md) |
| [`fastapi-ai-interview-prep`](fastapi-ai-interview-prep.md) | 100 self-written FastAPI/AI interview Q&A across 10 topics + a `quiz.py` mock-interview CLI | [docs](fastapi-ai-interview-prep.md) |
| [`raycast-extension-dev`](raycast-extension-dev.md) | Build/verify/ship Raycast extensions — the launchd PATH trap, the typecheck `ray build` skips, `MenuBarExtra` constraints, and the store checks `ray lint` never runs; ships a scaffolder + readiness checker | [docs](raycast-extension-dev.md) |
| [`python-project-best-practice`](python-project-best-practice.md) | Modern Python project conventions — uv + src layout, Tyro CLIs, loguru, ruff/type/pytest behind a Justfile, an AGENTS.md docs-drift gate; ships a six-profile scaffolder and a 26-check read-only legacy audit | [docs](python-project-best-practice.md) |

## Vendored skills

3rd-party skills cherry-picked because they fill a gap the local skills
don't cover, or because the upstream is the canonical authority on the
topic. The linked detail page shows what each skill teaches, upstream
provenance, and last-sync commit is tracked in `vendor.yaml`.

Vendored skills can be **flat** (`skills/vendor/<name>/`) or grouped into
a **series** (`skills/vendor/<series>/<name>/`). See
[Adding vendor skills](../workflows/adding-vendor-skills.md#series-grouping)
for how series work.

### Flat (notebooks + meta)

| Skill | Upstream | Detailed page |
|---|---|---|
| [`marimo-notebook`](marimo-notebook.md) | [marimo-team/skills](https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook) | [docs](marimo-notebook.md) |
| [`streamlit-to-marimo`](streamlit-to-marimo.md) | [marimo-team/skills](https://github.com/marimo-team/skills/tree/main/skills/streamlit-to-marimo) | [docs](streamlit-to-marimo.md) |
| [`anywidget`](anywidget.md) | [marimo-team/skills](https://github.com/marimo-team/skills/tree/main/skills/anywidget) | [docs](anywidget.md) |
| [`skill-creator`](skill-creator.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | [docs](skill-creator.md) |
| [`herdr`](herdr.md) | [herdrdev/herdr](https://github.com/herdrdev/herdr/tree/master/skills/herdr) | [docs](herdr.md) |

### Fullstack Next.js series

`series: fullstack-nextjs` — Next.js (App Router) + Supabase (Postgres) +
shadcn/ui + Tailwind CSS + design/testing skills. All from official orgs
(Vercel, vercel-labs, Supabase, Anthropic).

| Skill | Upstream | Detailed page |
|---|---|---|
| [`nextjs`](nextjs.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/nextjs) | [docs](nextjs.md) |
| [`shadcn`](shadcn.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/shadcn) | [docs](shadcn.md) |
| [`react-best-practices`](react-best-practices.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/react-best-practices) | [docs](react-best-practices.md) |
| [`vercel-storage`](vercel-storage.md) | [vercel/vercel-plugin](https://github.com/vercel/vercel-plugin/tree/main/skills/vercel-storage) | [docs](vercel-storage.md) |
| [`supabase`](supabase.md) | [supabase/agent-skills](https://github.com/supabase/agent-skills/tree/main/skills/supabase) | [docs](supabase.md) |
| [`supabase-postgres-best-practices`](supabase-postgres-best-practices.md) | [supabase/agent-skills](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices) | [docs](supabase-postgres-best-practices.md) |
| [`web-design-guidelines`](web-design-guidelines.md) | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | [docs](web-design-guidelines.md) |
| [`frontend-design`](frontend-design.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | [docs](frontend-design.md) |
| [`webapp-testing`](webapp-testing.md) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | [docs](webapp-testing.md) |

For the rules every local skill follows (layout, naming, scripts,
references), see [Conventions](../conventions.md). For how vendoring
works end-to-end, see [Adding vendor skills](../workflows/adding-vendor-skills.md).
