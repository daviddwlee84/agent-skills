# Conventions (standalone)

Minimum commit, branch, and merge conventions for forge-native-dev users
who do not have the `git-workflow` skill installed. If you do have
`git-workflow`, its `references/conventional-commits.md` is the full spec;
this file covers only the essentials.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <imperative subject>

<optional body — the "why">
```

### Types

| Type | When |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Neither fix nor feature |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `build` | Build system / dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance (not user-facing) |
| `revert` | Reverts a prior commit |

### Rules

- **Subject**: imperative mood, lowercase start, no trailing period,
  ≤72 chars. "add retry to client", not "Added retry." or "Adds…".
- **Body**: explain the "why" for non-trivial changes, wrapped ~72 cols.
- **Breaking change**: append `!` after type/scope — `feat!: drop v1 API`.
- **Language**: commit messages in English, even when the prompt is in
  another language. Code history is read by tooling and future collaborators.

## Branch naming

| Who | Pattern | Example |
|---|---|---|
| Human | `issue/<number>-<kebab-slug>` | `issue/42-add-oauth` |
| Agent | `agent/issue/<number>-<slug>` | `agent/issue/42-add-oauth` |
| Cursor/misc | `cursor/<desc>` | `cursor/dogfood-forge` |

The `issue/<N>-*` pattern ties the branch to its issue, enabling
`forge-cleanup.sh` and `forge-status.sh` to track alignment automatically.

## Linear history

Set these per-repo (or `--global`):

```bash
git config pull.rebase true      # rebase local work on pull
git config merge.ff only         # refuse merges that can't fast-forward
```

## Merge strategy

**Default: squash and merge.** One issue = one PR = one commit on `main`.

| Strategy | When |
|---|---|
| **Squash** | Default. Agent branches, vibe-coding, WIP-heavy PRs. |
| **Rebase** | Every commit in the PR is a curated, meaningful change. |
| **Merge commit** | Almost never. Only when branch topology matters. |

After squash-merge, the source branch's commits don't appear on `main`,
so `git branch --merged` won't list it. `forge-cleanup.sh` checks PR
status directly instead — always use it for cleanup, not `git branch -d`.

## Post-merge follow-up

After a PR merges:

1. **New branch from updated main** — `git switch main && git pull --rebase && git switch -c cursor/next-thing`
2. **New PR** — each PR is one logical change
3. **Do not** reuse the merged branch (history diverges after squash)
4. **Do not** try to reopen a merged PR (GitHub doesn't allow it)
5. Name branches for the issue they address, not the previous PR
