# Agent Skills

A personal collection of [agent skills](https://agentskills.io/home) — both
custom-authored and cherry-picked from upstream repos — installable as a
single package.

## Install

--8<-- "_snippets/install.md"

## What's in here

Two flavors of skills live under `skills/`:

- **`skills/local/`** — custom-authored skills maintained in this repo.
  See the [Skills overview](skills/index.md) for the index.
- **`skills/vendor/`** — third-party skills synced from upstream repos via
  the [`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
  manifest. See [Adding vendor skills](workflows/adding-vendor-skills.md).

The repo is also a live example of the
[`project-knowledge-harness`](skills/project-knowledge-harness.md) skill
applied to itself: [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md),
[`backlog/`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog),
and [`pitfalls/`](https://github.com/daviddwlee84/agent-skills/tree/main/pitfalls)
sit at repo root, with [`scripts/`](reference/scripts.md) wrapping the
validator/promoter/inbox toolkit.

## Where to go next

| If you want to… | Read |
|---|---|
| Install and try the skills | [Getting Started](getting-started.md) |
| Understand naming / layout rules | [Conventions](conventions.md) |
| Add a third-party skill | [Adding vendor skills](workflows/adding-vendor-skills.md) |
| Author a new local skill | [Creating local skills](workflows/creating-local-skills.md) |
| Capture a TODO or pitfall in a project | [Project memory workflow](workflows/project-memory.md) |
| Browse what skills exist | [Skills overview](skills/index.md) |
| Build a docs site for your own project | [Downstream docs stack recipe](reference/docs-stack-recipe.md) |
