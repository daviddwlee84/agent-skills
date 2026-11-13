# Pointer-only home repo

A **home repo** is an outer repository that holds shared context (agent
instructions, notes, runbooks) and *points at* other repositories without
recording their versions. It is the fallback when submodules do not fit; read
`decision-guide.md` first. Both kinds can coexist in one workspace.

## The manifest

Pointer children are `[repo "<name>"]` sections in `.superproject`, the same
git-config file that marks the root:

```ini
[workspace]
    mode = pointer              # `add` defaults to --pointer
    worktree-root = .worktrees
    map-file = docs/repos.md    # optional, see "Repo map"
[repo "docs-site"]
    path = repos/docs-site      # default repos/<name>
    url = https://example.com/org/docs-site.git
    branch = main               # default: the clone's origin/HEAD
    x-tier = reference
    x-role = Public documentation site
```

```bash
sp new my-home --mode pointer
sp add https://example.com/org/docs-site.git --role "Public documentation site" --tier reference
sp add https://example.com/org/infra.git ../infra --no-clone   # record now, clone later
```

`add` writes the section and clones (unless `--no-clone`). If `PATH` already
holds a clone whose `origin` matches the URL, it adopts it in place. It never
stages or commits.

## Where clones live

| Path | Behaviour |
|---|---|
| `repos/<name>` (default) | Inside the root, so an agent started there sees it. `add` gitignores it; `audit` reports `pointer-not-ignored` (warn) if the rule is lost and `pointer-tracked` (error) if files under it were committed. |
| `../x` | A sibling checkout. Nothing to ignore. Every collaborator needs the same layout. |
| `~/x` or absolute | Fits an existing personal layout. `audit` reports `pointer-path-absolute` (info): the manifest stops being portable. |

`audit` also reports `pointer-url-mismatch` (warn) when a clone's `origin`
differs from the manifest.

## Clone on demand

`init` never clones a pointer implicitly. It clones only children named on
the command line, selected by `--tier` or `--kind pointer`, or with `--all`.
A fresh clone of the home repo is therefore small; an agent clones what a task
needs (`init docs-site`). A directory with files but no `.git` is refused
(`foreign`), never overwritten.

## What works the same, and what does not

| Command | Pointer behaviour |
|---|---|
| `status` | POLICY `pointer`, GITLINK `-`, LAG = commits HEAD trails `origin/<branch>`. JSON adds `kind`; the top-level key stays `submodules`. |
| `pull NAME` | Fast-forward only, no `--force` needed. Not selected without a name. |
| `worktree`, `task`, `repair` | Same as submodules; the store is the clone's own `.git`. Worktrees go to `R/<name>/<branch>` and `R/_tasks/<task>/<name>`. |
| `bump`, `preflight`, `ci-plan` | Refused: a pointer has no gitlink. If a version must be recorded, add the repository as a submodule. |

## Repo map

`new`, `add` and `adopt` keep a marker-delimited **repo map** in the agents
file (`AGENTS.md`, else `CLAUDE.md`): one row per child with name, `x-role`,
path, kind or policy, tier, and the command that fetches it when missing. It
covers submodule and pointer children alike.

With many repositories the map costs context in every session. Set
`workspace.map-file` and the full map, grouped by tier, moves to that file;
the agents file keeps one line with the count per tier and a link
(progressive disclosure). `audit` reports `repo-map-stale` (warn) when the
map no longer matches the manifests, and `repo-map-large` (info) when more
than 25 entries are inline. Rerun `adopt` to refresh it.

## What goes where

| Outer home repo | Each child |
|---|---|
| Cross-repo AGENTS.md block and repo map | Its own AGENTS.md/CLAUDE.md (authoritative inside it) |
| Notes and runbooks that span repositories, dated or tied to a commit | Code, its CI, its issues and PRs |
| Agent session history for cross-repo work | Its own history |

Because nothing pins versions, write the commit or date a cross-repo note was
observed against.

## Harness loading

Agents read the home repo's instructions only when started at its root. A
clone under `repos/` contributes its own `CLAUDE.md` when the agent reads
files there; a clone outside the root needs add-dir, and its instructions load
only under the rules in `agent-entry.md`.

## Converting a pointer to a submodule

1. Commit and push any work in the clone; note its `branch`.
2. Remove the `[repo "<name>"]` section: `git config -f .superproject --remove-section repo.<name>`.
3. Move the clone aside (`mv repos/<name> /tmp/<name>.bak`) and drop its ignore rule.
4. `sp add <url> <path> --submodule --policy pin` (or `track`).
5. Run `adopt` to refresh the template and repo map; review, commit.
