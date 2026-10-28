# Adopt superproject-workspace in existing superprojects

**Status**: P2 (follow-up to #33)
**Effort**: M per superproject
**Related**: [`skills/local/superproject-workspace`](../skills/local/superproject-workspace/SKILL.md) · `references/case-patterns.md`

## Context

2026-10-28: `superproject-workspace` shipped with `audit` and `adopt`. A
read-only smoke run against the maintainer's two reference superprojects (an
umbrella and a workspace hub) found:

- no policy keys
- an umbrella child 9 commits ahead of its recorded pointer
- several hub gitlinks reachable from no `origin` branch in local refs (re-check with `audit --fetch`)
- checkouts sitting on feature branches with dirty trees
- child paths hard-coded into duplicated sh/pwsh recipes

The concrete per-repo checklists live in each superproject's own issue
tracker, because those repos are private.

## Generic adoption checklist

1. `audit --fetch` and save the report. Resolve every `gitlink-unreachable`
   error first by pushing the child commit or moving the pointer. A fresh
   clone fails on these.
2. Agree policies with the owner:
   - children the outer repo should follow → `track`
   - deployed or known-good baselines → `pin`, with `branch` set to the
     baseline line
   - references and rarely used children → `lazy`
3. `adopt --dry-run --policy-default pin --set <child>=track:pr ...`, review,
   then `adopt` (`--with-ci` once a `SUBMODULE_TOKEN` exists for private
   children). Install the skill globally first (`npx skills add ...`), because
   the recipes reference it instead of copying the CLI.
4. Replace hand-written submodule recipes with the `sub-*` block. Keep
   repo-specific recipes (deploy, build), but make them read paths from the CLI
   rather than hard-coding them.
5. Retire bespoke init scripts that the policy keys and `init --tier` now cover.
6. Move ongoing child feature work into `.worktrees/<child>/<branch>`, or
   document why it is kept outside.
7. Commit the adoption as one outer commit. Run `audit --strict` in the
   superproject's CI.
