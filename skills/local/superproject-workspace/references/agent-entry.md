# The outer repo as an agent entry point

## Instruction layering

- **Outer `AGENTS.md`/`CLAUDE.md`** governs *cross-repo* work only. Keep the
  `adopt` block in it (outer repo rules, commit inside-out, one outer commit,
  worktrees, pins) and the generated repo map of which child owns what.
- **Each child's own instruction file** stays authoritative inside that
  child. Say so explicitly in the outer file.
- Do not copy child instructions upward; link to them. Copies drift exactly
  like gitlinks do.

## What each harness actually loads

Know these before relying on a file being read:

| Situation | Claude Code | Codex |
|---|---|---|
| Session started at the root | `CLAUDE.md` in the cwd and its parents. It reads `AGENTS.md` only when there is **no** `CLAUDE.md` in the cwd or above. | `AGENTS.md` along the path from the repo root to the cwd |
| Child directory under the root | Its `CLAUDE.md` loads when the agent reads files in that directory, not when it only greps | `AGENTS.md` files along the path to the files it works on |
| `--add-dir` directory | `CLAUDE.md` only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`; never `AGENTS.md` | n/a |
| Cloud Projects | Each repo root's `CLAUDE.md` and `.claude/rules`; not `.claude/skills` | per its own docs |

Consequences:

- If the root has both files, Claude Code reads only `CLAUDE.md`. Put
  `@AGENTS.md` in `CLAUDE.md`, or make `CLAUDE.md` a symlink to `AGENTS.md`.
  `audit` reports `agents-not-loaded` when the managed block sits only in an
  `AGENTS.md` that Claude Code ignores.
- A child whose only instruction file is `AGENTS.md` is invisible to Claude
  Code. The outer block tells agents to read it; better, give the child a
  `CLAUDE.md` with `@AGENTS.md`.
- Pointer clones outside the root contribute nothing unless added with
  add-dir and the environment variable above.

## Where the child map and project memory live

These are choices, not rules. The defaults:

- **Child roles**: the generated repo map in the agents file (from `x-role`);
  with many repos, `workspace.map-file` moves the full map to its own file.
  See `home-repo.md`.
- **Cross-repo memory** (notes, pitfalls, runbooks, session history): in the
  outer repo, because it belongs to no single child. A child's own memory
  stays in the child.

## Root context that earns its place

What makes an outer repo better than "a folder of clones" is content that
belongs to *no single child*:

- a cross-repo context graph (entities, relations, dated observations)
- `pitfalls/` for traps that span repos (version skew, protocol mismatches)
- runbooks that orchestrate several children (deploy, parity checks)
- agent session history, since cross-repo sessions have no other home

Record facts with the gitlink SHA (submodules) or the commit/date (pointers)
they were observed against. A note like "service X does Y" goes stale when
the child moves.

## Projects and add-dir

A Project or `--add-dir` gives similar context breadth without an outer repo,
but provides no versioned snapshot and no home for root content. Use them for
one-off reads; use an outer repo when the combination itself, or the root
knowledge, matters.

## Session start checklist (put in AGENTS.md)

1. `sp status --fetch`
2. Read the target child's own instructions.
3. Branch work goes in `worktree add` or `task open`, from the main checkout,
   never in the child checkout itself.
