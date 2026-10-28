# The superproject as an agent entry point

## Instruction layering

- **Outer `AGENTS.md`/`CLAUDE.md`** governs *cross-repo* work only. Keep the
  `adopt` block in it (commit inside-out, one outer commit, worktrees, pins).
  Add a short map of which child owns what.
- **Each child's `AGENTS.md`** stays authoritative inside that child. Agents
  must read it before editing there; say so explicitly in the outer file.
  Claude Code loads nested `CLAUDE.md` files on demand when it touches files
  in that directory; Codex reads `AGENTS.md` along the path. Neither harness
  guarantees this for files the agent only greps.
- Do not copy child instructions upward; link to them. Copies drift exactly
  like gitlinks do.

## Root context that earns its place

What makes a superproject better than "a folder of clones" is content that
belongs to *no single child*:

- a cross-repo context graph (entities, relations, dated observations)
- `pitfalls/` for traps that span repos (version skew, protocol mismatches)
- runbooks that orchestrate several children (deploy, parity checks)
- agent session history (SpecStory), since cross-repo sessions have no other home

Record facts with the gitlink SHA or date they were observed against. A note
like "service X does Y" goes stale when the pointer moves.

## Claude / Codex Projects and add-dir

A Project or `--add-dir` gives similar context breadth without submodules,
but provides no versioned snapshot and no home for root content. Use them for
one-off reads; use the superproject when the combination itself, or the root
knowledge, matters.

## Session start checklist (put in AGENTS.md)

1. `uv run --script scripts/superproject.py status --fetch`
2. Read the target child's AGENTS.md.
3. Branch work goes in `worktree add`, never in the submodule checkout.
