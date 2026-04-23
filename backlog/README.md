# Backlog Research

Long-form research, design notes, and paused evaluation for items listed in
[`../TODO.md`](../TODO.md). One file per topic, named with a slug that matches
the TODO entry.

## Why this exists

`TODO.md` is the index of deferred work. This folder is the research layer that
keeps the context behind those items: prior investigation, trade-offs, blockers,
and decisions that should survive beyond one chat session.

This repo's public install surface lives under [`skills/`](../skills/). Files in
`backlog/` are tracked repo metadata for maintainers and agents, not part of the
published skill collection layout.

## When to add a doc here

Add a `backlog/<slug>.md` file when any of these apply:

- The TODO item is in `P?` and needs evaluation before it can be prioritized
- Meaningful troubleshooting happened but the fix was deferred
- Multiple implementation options were compared and the trade-offs matter later
- External blockers or missing context would make future re-investigation costly
- The implementation is `[L]` or `[XL]` and needs a design-oriented handoff

## Index

Keep entries alphabetical and point them back to the matching `TODO.md` item.

| Slug | Status | TODO entry |
|---|---|---|
| `financial-data-sources` | queued | `P?` "Financial data sources skill set" |
