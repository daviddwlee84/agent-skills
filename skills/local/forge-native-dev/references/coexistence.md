# Coexistence with Other Skills

## Decision tree

```
Is there a GitHub/GitLab remote?
├── No  → use git-workflow (+ optionally project-knowledge-harness)
└── Yes → is gh/glab installed and authenticated?
    ├── No  → use git-workflow (recommend installing the CLI)
    └── Yes → does the user prefer local-first or hosted-first?
        ├── Local-first  → project-knowledge-harness + git-workflow
        └── Hosted-first → forge-native-dev (this skill)
```

## forge-native-dev vs git-workflow

| Aspect | git-workflow | forge-native-dev |
|---|---|---|
| Scope | Git mechanics (commits, branches, merges) | Forge lifecycle (issues, PRs, cleanup) |
| Requires | git | git + gh/glab |
| Branching | `feat/`, `fix/`, `agent/` | `issue/<N>-*`, `agent/issue/<N>-*` |
| Worktrees | Generic parallel isolation | Issue-linked, auto-created/destroyed |
| PR creation | Delegate to `create-pull-request` skill | Built-in via `forge-worktree.sh finish` |
| Branch cleanup | `branch-status.sh` (diagnosis) | `forge-cleanup.sh` (diagnosis + action) |
| Backlog | Not covered (defer to PKH) | Issues on the forge |

### If both are installed

On first ambiguous operation, the agent asks the user's preference.
Default: `forge-native-dev` for anything involving the remote.

`git-workflow` is still useful for:
- Commit message conventions (Conventional Commits)
- AI provenance trailers (`AI-Assisted-By`, etc.)
- SemVer release tagging
- The lazygit cheatsheet

These don't conflict with `forge-native-dev`. The overlap is specifically
in branching, PR creation, and cleanup.

**Recommendation**: install both, let `forge-native-dev` handle the forge
layer, and `git-workflow` handle the commit/release layer.

## forge-native-dev vs project-knowledge-harness

| Aspect | project-knowledge-harness | forge-native-dev |
|---|---|---|
| Backlog | `TODO.md` (file-based, portable) | Issues (hosted, collaborative) |
| Research | `backlog/*.md` (in-repo) | Discussions / issue threads |
| Pitfalls | `pitfalls/*.md` (in-repo) | `pitfalls/*.md` (in-repo — same) |
| Visualization | `todo-kanban.sh` | GitHub Projects / GitLab Boards |
| Cross-referencing | Manual links | Auto-linked |
| Offline access | Full | Limited to cached data |
| td integration | Yes (optional) | No (not needed — Issues are the tracker) |

### One workflow per project, not both

Using both creates duplicate sources of truth. A "maybe later" idea ends
up in both `TODO.md` and an Issue, and they drift apart.

### Migration: PKH -> forge-native-dev

1. **Run `forge-init.sh`** to set up the forge-native workflow.

2. **For each active `TODO.md` item**, create an Issue:

   ```bash
   # Example: migrate a P2 item
   bash scripts/forge-issue.sh create \
     --title "Try Rspress for docs" \
     --body "Evaluate AI-native docs framework alternative.

   Migrated from TODO.md P? lane." \
     --label "backlog" --label "priority/P3"
   ```

3. **For `backlog/*.md` research docs**:
   - Short docs: paste into issue body
   - Long docs: create a Discussion linking to the file, keep the file

4. **Keep `pitfalls/`** in-repo — they need grep-ability.

5. **Remove PKH guidance** from `AGENTS.md`:
   Delete the block between `<!-- project-knowledge-harness:... -->` markers.

6. **Optionally remove `TODO.md`** once all items are migrated.
   Keep `backlog/` and `pitfalls/` directories.

### Migration: forge-native-dev -> PKH

If you decide to go back to local-first:

1. Export open issues to `TODO.md` entries
2. Run PKH's `init.sh`
3. Remove forge-native-dev guidance from `AGENTS.md`

## forge-native-dev vs create-pull-request (vendored)

The vendored `create-pull-request` skill is a standalone PR creation guide.
`forge-native-dev` includes PR creation as part of its lifecycle
(`forge-worktree.sh finish` and `forge-pr.sh create`).

If both are installed, prefer `forge-native-dev`'s PR flow because it
automatically links the PR to the originating issue.

## Role model

The skill distinguishes two roles based on actual repository permissions,
not repo ownership:

| Role | Who | Detection |
|---|---|---|
| **Maintainer** | Repo owner, org member with write access, collaborator with push | GitHub: `repo.permissions.push == true`; GitLab: `access_level >= 30` (Developer+) |
| **Contributor** | Fork-based contributor, read-only org member, guest | Everything else |

This means a core developer in an organization who has write access is
correctly detected as `maintainer` — they can create labels, assign issues,
and merge PRs, even though they didn't create the repo.

### Override

If auto-detection gives the wrong answer (e.g., API rate-limited, SSO
not configured):

```bash
# At init time
forge-init.sh --role maintainer

# At runtime (env var)
export FORGE_ROLE_OVERRIDE=maintainer
```

### What changes by role

| Action | Maintainer | Contributor |
|---|---|---|
| `forge-init.sh` creates labels | Yes | Skipped |
| `forge-issue.sh backlog` applies priority labels | Yes | Priority noted in body text |
| `forge-worktree.sh start` assigns issue + adds label | Yes | May fail silently (no write access) |
| `forge-pr.sh merge` | Yes | Cannot merge (expected — maintainer merges) |
| Issue templates scaffolded | Yes | Yes (they're just repo files) |
| Git config set | Yes | Yes (local config only) |

## Detecting which workflow is active

Agents can detect the active workflow by checking for sentinel markers:

```bash
# PKH is active if TODO.md has lane headers
grep -q '^## P[123?]' TODO.md 2>/dev/null && echo "PKH active"

# forge-native-dev is active if AGENTS.md has its sentinel
grep -q 'forge-native-dev:guidance' AGENTS.md 2>/dev/null && echo "forge-native-dev active"

# git-workflow is active if its commit template is configured
git config commit.template 2>/dev/null | grep -q 'git-workflow' && echo "git-workflow active"
```
