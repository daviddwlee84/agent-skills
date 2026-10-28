# Plan: `superproject-workspace` skill

## Context

In AI-assisted development an agent often needs one entry point with context and edit access across many repos. A real monorepo couples the repos too tightly. A **superproject of git submodules** keeps them decoupled, but it drifts over time:

- child PRs merge and the gitlink silently falls behind
- children sit detached or dirty
- a pointer can reference an unpushed commit
- worktrees get messy
- each superproject grows its own ad-hoc justfile

The user has two working examples, which follow two different patterns:

- **dotfiles-all** is an *umbrella*. All 5 children are owned by the user and track `main`. Strong points: the `gitlink-preflight` check that a commit is reachable from `origin/main`, the ff-only `submodule-pull-main`, and inside-out commits. Weak points: no scheduled bump, 5 hard-coded paths, and every recipe duplicated for sh and pwsh.
- **Tadronaut-Mono-Repo** is a *workspace hub*. Children are tiered core/personal/references. Lazy init happens through `scripts/init_submodules.py`, and gitlinks are reproducible pins ("latest ≠ reset to main"). Experiments run in external worktrees, and a `context/` knowledge graph lives at the root. Weak points: no rule for when a pin moves forward, and no report of how far behind each child is.

The user has more, older and less agentic superprojects. The goal is one skill that encodes best practice for both patterns, and that can audit and upgrade the existing repos.

## Decisions (agreed with the user)

| Topic | Decision |
|---|---|
| Scope | Cover both patterns with one **per-submodule policy**. An umbrella is the special case where every child is `track`. |
| Policy storage | Custom keys in `.gitmodules`, read and written with `git config -f .gitmodules` |
| Bump mode | Each submodule chooses: `pr` (scheduled CI opens a PR), `direct` (CI commits to main after preflight), or `manual` |
| Worktrees | Child feature branches go in `.worktrees/<sub>/<branch>`, created from the child's own gitdir and gitignored. They stay inside the agent's entry point. Never use superproject worktrees. |
| No-submodule alternative | Covered by the decision guide only: manifest + gitignored clones, or Claude/Codex Project add-dir |
| Tooling | One PEP 723 Python CLI run via `uv run`. It works cross-platform, which removes the duplicate sh/pwsh recipes. Thin justfile wrapper, `--json` and `--dry-run` on every subcommand. |
| Adoption | `audit` (read-only) plus `adopt` (writes policy keys, AGENTS.md block, recipes, optional CI) |
| Deliverable | The skill, plus a list of improvements for the two example repos. Those repos are not modified in this task. |

### `.gitmodules` schema

```ini
[submodule "tarlin"]
    path = submodules/tarlin
    url = https://github.com/tadronaut/tarlin.git
    branch = main          # native git key; the tracking branch
    x-policy = track       # track | pin | lazy
    x-bump = pr            # pr | direct | manual   (pin/lazy => manual enforced)
    x-tier = core          # free-form grouping: core | personal | reference | ...
    update = none          # set for lazy: native git skip on plain `submodule update`
```

Semantics:

- `track`: may follow `origin/<branch>` by fast-forward only.
- `pin`: moves only on an explicit `bump --reason`. The reason goes into the commit body.
- `lazy`: not initialized by default and never bumped automatically. It is initialized on demand without recursion.

## Skill layout: `skills/local/superproject-workspace/`

- `SKILL.md`
  - when to use it
  - the core invariant: a gitlink is a commit, not a branch, so drift is expected and must be made visible and machine-bumped
  - policy table, daily workflows (start / develop in a child / bump / review)
  - gotchas
  - CLI quick reference
- `scripts/superproject.py` (PEP 723, stdlib only, Python ≥3.10). The subcommands:
  - `status [--fetch] [--json]`: for each submodule, shows policy and tier, whether it is initialized, gitlink vs HEAD, branch or detached, dirty, ahead/behind `origin/<branch>`, whether the gitlink is reachable from origin, and its worktrees.
  - `init [--tier T] [names…] [--recursive]`: policy-aware init. Lazy submodules are initialized only by name or tier, using `--checkout` to override `update=none`.
  - `pull [names…]`: fast-forwards `track` submodules. It reuses the dotfiles-all safety rules: refuse on diverged branch, unreachable detached commit, or dirty tree. It refuses `pin` unless `--force`.
  - `bump [names…|--all-track] [--reason] [--commit] [--dry-run]`: runs preflight, stages the affected gitlinks together, and creates **one outer commit** whose message includes the `--submodule=log` summary.
  - `preflight`: checks that staged gitlinks are clean, pushed, and reachable from `origin/<branch>`. It also serves as the pre-commit hook.
  - `worktree add|list|remove <sub> <branch> [--base REV]`: manages `.worktrees/<sub>/<branch>` and ensures the `.gitignore` entry exists.
  - `audit [--json]`: reports
    - missing policy keys
    - drift and lag
    - unreachable pointers
    - stale worktrees
    - missing AGENTS.md block
    - hard-coded submodule paths in the justfile
    - missing CI for `pr`/`direct` submodules
  - `adopt [--dry-run] [--policy-default …] [--with-ci]`: writes policy keys, inserts the marker-delimited AGENTS.md block, adds the justfile snippet and `.gitignore` entry, and optionally the workflow.
  - `ci-plan --json`: emits the `pr` and `direct` bump sets for the workflow.
- `assets/`
  - `justfile.snippet`: thin recipes that call the CLI
  - `agents-block.md.template`: the cross-repo contract. It covers reading the child's AGENTS.md first, committing inside-out, one outer pointer commit per cross-repo change, and "latest ≠ reset pins". Marker-delimited, like project-knowledge-harness.
  - `superproject-bump.yml`: scheduled plus `workflow_dispatch`. It runs `ci-plan`. `pr` submodules go to a fixed branch `chore/submodule-bump`, using the same pattern as this repo's `.github/workflows/vendor-sync.yml`. `direct` submodules push to main after preflight.
  - `child-dispatch.yml`: optional, for an immediate bump through `repository_dispatch`
  - `pre-commit-hook.sh`
- `references/`
  - `decision-guide.md`: when to choose a real monorepo, a submodule superproject, a manifest with gitignored clones, or Project add-dir
  - `policies.md`: the policy model with examples of umbrella vs hub configurations
  - `worktrees.md`: explains why superproject worktrees fail (each needs every submodule re-initialized) and gives the child-worktree recipe
  - `ci-bump.md`: tokens and deploy keys for private and GitLab children, and the `GITHUB_TOKEN` → no-validate pitfall already documented in CLAUDE.md
  - `agent-entry.md`: AGENTS.md layering, Claude/Codex Projects, and a root `context/` directory
  - `gotchas.md`, grep-able by symptom. Covers:
    - "modified: sub (new commits)"
    - detached HEAD after update
    - `git pull` not updating submodules / `submodule.recurse`
    - nested private submodules
    - a URL changed without running `submodule sync`
  - `case-patterns.md`: anonymized umbrella and hub patterns. No private repo names, customers, or hosts, because this repo is public.
- `tests/test_superproject.py`: unittest against temporary local bare-repo fixtures. Covers status, pull refusal cases, bump/preflight unreachable detection, lazy init, worktree add/remove, and audit/adopt idempotency.

## Repo integration (per CLAUDE.md)

- Open a GitHub issue first, then `bash skills/local/forge-native-dev/scripts/forge-worktree.sh start <n>`.
- Scaffold with `bash skills/local/skill-author/scripts/new-skill.sh --local --no-symlinks superproject-workspace`. It is downstream-only, so it gets no `.claude/skills` link.
- Add `./local/superproject-workspace` to the `version-control` plugin in `skills/.claude-plugin/marketplace.json`.
- Add bilingual docs pages `docs/skills/superproject-workspace.md` and `.zh-TW.md`, following existing pages such as `docs/skills/agent-history-hygiene.md`. Add a nav entry if mkdocs.yml lists the pages explicitly.
- Cross-link from `skills/local/git-workflow/references/worktrees-parallel-agents.md` and from forge-native-dev's `coexistence.md`.
- Finish with `forge-worktree.sh finish <n>` and squash-merge the PR.

## Improvement checklists (delivered as a report, not applied)

Write `backlog/superproject-workspace-adoption.md`. It holds generic checklists only; private details stay out.

- **dotfiles-all**:
  - add `x-policy=track` and `x-bump` keys
  - replace the 5 hard-coded paths and the duplicated sh/pwsh recipes with CLI calls
  - add a scheduled bump workflow
  - remove the stale `dotfiles` path in the `submodule-diff` pathspecs
- **Tadronaut**:
  - map core → `pin`/`track` and personal/references → `lazy`, so that `update=none` replaces most of `init_submodules.py`
  - add `status` lag reporting
  - move external worktrees to `.worktrees/`, or keep them and document why
  - keep `context/` as is
- **Older superprojects**: run `audit`, then `adopt --dry-run`.

## Verification

1. `uv run skills/local/superproject-workspace/scripts/superproject.py --help`, plus each subcommand's `--help`.
2. `uv run python -m unittest skills/local/superproject-workspace/tests/test_superproject.py -v`. This covers the fixture superproject with track, pin, and lazy children.
3. Read-only smoke test on local clones of dotfiles-all and Tadronaut: `status --json` and `audit` must report sensible results, and `adopt --dry-run` must show a plausible diff without writing anything.
4. `make validate`, which covers frontmatter, marketplace, and TODO format. Also `make docs-build`.
5. Lint the CI template with `actionlint` if it is installed.
