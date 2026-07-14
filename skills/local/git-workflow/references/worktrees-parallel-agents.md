# Worktrees for parallel agents

Read this before setting up parallel Claude Code sessions/agents, or when
debugging a worktree that's missing a gitignored file (like `.env`) or won't
clean up. Based on the official
[Claude Code worktrees docs](https://code.claude.com/docs/en/worktrees) and
[`git worktree`](https://git-scm.com/docs/git-worktree).

## Table of contents

1. [Why worktrees](#why-worktrees)
2. [Starting a worktree](#starting-a-worktree)
3. [Choosing the base branch](#choosing-the-base-branch)
4. [Copying gitignored files (`.worktreeinclude`)](#copying-gitignored-files-worktreeinclude)
5. [Isolating subagents](#isolating-subagents)
6. [SpecStory separation bonus](#specstory-separation-bonus)
7. [Cleanup](#cleanup)
8. [Manual worktrees & non-git VCS](#manual-worktrees--non-git-vcs)

---

## Why worktrees

A git worktree is a separate working directory with its own files and branch,
sharing the same repo history and remote. Running each parallel agent/session
in its own worktree means edits in one never touch another — one terminal
builds a feature while a second fixes a bug, with zero file collisions.

## Starting a worktree

```bash
claude --worktree feature-auth   # or -w
# → creates .claude/worktrees/worktree-feature-auth/ on branch worktree-feature-auth
claude --worktree                # omit the name → generates e.g. bright-running-fox
```

You can also ask Claude to "work in a worktree" mid-session (it uses the
`EnterWorktree` tool). **Add `.claude/worktrees/` to `.gitignore`** so worktree
contents don't appear as untracked files in your main checkout.

## Choosing the base branch

- Default: worktrees branch from `origin/HEAD` (your default branch), so they
  start from a clean tree matching the remote.
- To branch from your **local HEAD** (carrying unpushed commits / feature-branch
  state — useful for isolating subagents on in-progress work), set in settings:

```json
{ "worktree": { "baseRef": "head" } }
```

  Only `"fresh"` (default) or `"head"` are accepted — not arbitrary refs.
- Branch from a specific PR: `claude --worktree "#1234"` →
  `.claude/worktrees/pr-1234`.

## Copying gitignored files (`.worktreeinclude`)

A worktree is a fresh checkout, so untracked files like `.env` are **not**
present. Add a `.worktreeinclude` at the repo root to copy them in
automatically. It uses `.gitignore` syntax and copies **only files that match a
pattern *and* are gitignored** — tracked files are never duplicated.

```text
# .worktreeinclude — gitignored files to carry into new worktrees
.env
.env.local
config/secrets.json
```

**Key correction to a common misconception:** a committed
`.vscode/settings.json` is *tracked*, so it's already in the worktree checkout
— listing it here does nothing. Only put genuinely-ignored files here. Applies
to `--worktree`, subagent worktrees, and desktop parallel sessions.

## Isolating subagents

Give parallel subagents their own worktrees so their edits don't conflict:

- Ask Claude to "use worktrees for your agents", or
- set it permanently on a custom subagent with frontmatter:

```yaml
---
name: my-agent
isolation: worktree
---
```

Each subagent gets a temporary worktree, removed automatically when it finishes
without changes. Subagent worktrees use the same base branch as `--worktree`.

## SpecStory separation bonus

SpecStory tracks transcripts by **directory**, not branch. Because each
worktree is a fresh directory, parallel agents each accumulate their chat
history under their own `.specstory/` — a clean cut that avoids interleaving
transcripts from concurrent sessions.

## Cleanup

On exiting a worktree session:

- **No changes/commits**: worktree + branch removed automatically (named
  sessions prompt so you can keep them).
- **Uncommitted changes / untracked / new commits**: Claude prompts to keep or
  remove.
- **Non-interactive `-p` runs**: not cleaned up automatically — remove with
  `git worktree remove` (add `--force` if it has uncommitted work).

Subagent/background worktrees are swept once older than `cleanupPeriodDays`,
provided they have no uncommitted changes/untracked files/unpushed commits.

## Manual worktrees & non-git VCS

Full manual control:

```bash
git worktree add ../proj-feature-a -b feature-a   # new branch
git worktree add ../proj-bugfix bugfix-123        # existing branch
git worktree list
git worktree remove ../proj-feature-a
```

Remember to reinitialize the dev environment in each new worktree (install
deps, create venvs). For **non-git VCS** (SVN/Perforce/hg), configure
`WorktreeCreate`/`WorktreeRemove` hooks — note that `.worktreeinclude` is **not
processed** when a custom hook replaces the default git logic, so copy local
config files inside the hook script instead.
