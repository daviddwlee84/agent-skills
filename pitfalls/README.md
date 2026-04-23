# Pitfalls

Past traps we have already debugged. This is a symptoms-first knowledge base:
when the same failure appears again, grepping the symptom here should land on
the root cause and workaround faster than re-debugging from scratch.

This repo's public install surface lives under [`skills/`](../skills/). Files in
`pitfalls/` are tracked repo metadata for maintainers and agents, not part of
the published skill collection layout.

## Pitfalls vs the rest

| Surface | Time direction | Question it answers | Access pattern |
|---|---|---|---|
| `TODO.md` | Future | "What might we do later?" | Read by priority |
| `backlog/<slug>.md` | Future | "What analysis already happened?" | Follow links from `TODO.md` |
| `pitfalls/<slug>.md` | Past | "Have we seen this symptom before?" | Grep by symptom |
| `CLAUDE.md` / `AGENTS.md` | Present | "What rules must agents follow?" | Read top to bottom |

A pitfall graduates into a hard agent rule when the trap silently corrupts
state, recurs across sessions or machines, or has a workaround that is too easy
to forget. When that happens, keep the pitfall doc as history and link to it
from `CLAUDE.md`.

## When to add a pitfall doc

Add `pitfalls/<slug>.md` when all of the following are true:

- The debugging session took long enough that the context is worth preserving
- The symptom would be hard to rediscover from normal docs or web search alone
- A future maintainer or agent could realistically hit the same problem again

Each pitfall doc should capture the verbatim symptom, root cause, workaround,
and prevention guidance.

## Index

| Slug | Symptom keywords | Status |
|---|---|---|
| (none yet) | | |

## Cross-referenced pitfalls

| Trap | Lives in | Why not here |
|---|---|---|
| (none yet) | | |
