# Evaluate remaining mattpocock/skills for engineering-fundamentals

**Status**: P? (deferred)
**Effort**: M
**Related**: `TODO.md` · [`docs/reference/mattpocock-skills.md`](../docs/reference/mattpocock-skills.md) · `vendor.yaml` (`engineering-fundamentals` series) · `skills/.claude-plugin/marketplace.json`

## Context

2026-07-17 — while adding the [Matt Pocock deep-dive docs page](../docs/reference/mattpocock-skills.md)
we re-synced the vendored `engineering-fundamentals` series to current upstream
and grew it **9 → 15** to vendor the full end-to-end flow
(grill → spec → tickets → implement → review) plus its cross-skill dependencies
(`grilling`, `domain-modeling`, `codebase-design`). `mattpocock/skills` has many
more skills we deliberately left upstream. This item tracks whether any of them
should join the series later.

## Investigation

Current vendored set (15, `series: engineering-fundamentals`): `grill-with-docs`,
`grilling`, `domain-modeling`, `codebase-design`, `to-spec`, `to-tickets`,
`wayfinder`, `implement`, `tdd`, `code-review`, `diagnosing-bugs`, `triage`,
`improve-codebase-architecture`, `prototype`, `zoom-out` (frozen).

Two vendored skills still reference an un-vendored skill (accepted, documented):

- `wayfinder` → `/research` (delegated research sub-agents)
- flow → `/setup-matt-pocock-skills` (soft; each skill defaults to a local-markdown tracker)

Upstream skill inventory captured via
`gh api repos/mattpocock/skills/git/trees/main?recursive=1` (2026-07-17).

## Options considered (candidate skills, not yet vendored)

| Candidate | Bucket | Lean | Why |
|---|---|---|---|
| `setup-matt-pocock-skills` | `engineering/` | maybe | Bootstraps the issue-tracker/label/docs layout the flow's soft deps expect. Opinionated per-repo setup — vendoring it makes the tracker-backed flow turnkey, but imposes Matt's conventions. **Top candidate.** |
| `research` | `engineering/` | maybe | Would close `wayfinder`'s `/research` dep. Overlaps the vendored `deep-research` (199-biotech) — decide whether to adopt Matt's or adapt wayfinder to `/deep-research`. |
| `resolving-merge-conflicts` | `engineering/` | maybe | Hunk-by-hunk conflict resolution. Overlaps the local `git-workflow` scope; check for genuine gap. |
| `ask-matt` | `engineering/` | skip | Router over Matt's own skills — redundant once the flow is known. |
| `grill-me` | `productivity/` | skip | User-facing wrapper of `grilling` (already vendored). |
| `handoff`, `teach` | `productivity/` | skip | Niche productivity workflows outside the build loop. |
| `writing-great-skills` | `productivity/` | skip | Duplicates local `skill-author`. |
| `misc/*` | `misc/` | skip | `git-guardrails-claude-code`, `setup-pre-commit`, `migrate-to-shoehorn`, `scaffold-exercises` — narrow / host-specific. |
| `deprecated/*`, `in-progress/*`, `personal/*` | — | skip | Upstream marks these unstable or personal. |

## Current blocker / open questions

Deferred, not blocked. Open questions:

- Vendor `setup-matt-pocock-skills` (turnkey tracker flow) vs. keep the soft-dep
  default (local-markdown tracker)? Trade-off: convenience vs. imposing conventions.
- For `wayfinder`'s `/research`: vendor Matt's `research`, or rewire wayfinder to
  the vendored `deep-research`?

## Decision (if any)

`2026-07-17 deferred` — vendored the core flow only (15 skills). Re-evaluate the
`maybe` candidates above when someone actually adopts the tracker-backed flow.

## References

- [`docs/reference/mattpocock-skills.md`](../docs/reference/mattpocock-skills.md) — the deep-dive (flow + full skip list)
- Upstream: <https://github.com/mattpocock/skills>
- Video: *"Learn the whole flow, end-to-end"* — <https://youtu.be/M6mYodf0dJM>
