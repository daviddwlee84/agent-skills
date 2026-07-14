# lazygit cheatsheet

Read this when you'd rather drive git through [lazygit](https://github.com/jesseduffield/lazygit)
than raw CLI — a terminal UI that makes staging, committing, rebasing, and
branch work visual. This is a **learning aid**: it lowers the barrier while
you're getting fluent with git, and can be trimmed once the plain commands are
second nature.

## Table of contents

1. [Why lazygit](#why-lazygit)
2. [Layout & navigation](#layout--navigation)
3. [Everyday flow](#everyday-flow)
4. [Branches](#branches)
5. [History & rewriting](#history--rewriting)
6. [Stash & remotes](#stash--remotes)
7. [When to drop back to the CLI](#when-to-drop-back-to-the-cli)

---

## Why lazygit

It shows working-tree, staged, branches, commits, and stash side by side, so
the *state* git is in is visible instead of imagined. Interactive rebase,
partial staging, and amend — the operations most likely to go wrong from
memory — become point-and-confirm. Install: `brew install lazygit`, then run
`lazygit` inside a repo.

## Layout & navigation

Panels (left, top→bottom): **Status**, **Files**, **Branches**, **Commits**,
**Stash**; the right pane shows the diff/detail.

- `Tab` / `[` `]` — cycle panels; number keys `1`–`5` jump to a panel.
- `↑`/`↓` or `j`/`k` — move within a panel; `Enter` — descend into an item.
- `?` — context help (shows every keybinding for the focused panel).
- `x` — open the menu of actions for the current panel.
- `q` — quit.

## Everyday flow

In the **Files** panel:

- `Space` — stage/unstage the selected file (or hunk/line when you `Enter` into
  a file to stage partially).
- `a` — stage/unstage **all**.
- `c` — commit staged changes (opens the message editor; follow
  [Conventional Commits](conventional-commits.md)).
- `A` — amend the last commit with staged changes.
- `d` — discard changes (destructive — confirm carefully).

## Branches

In the **Branches** panel:

- `Space` — checkout the selected branch.
- `n` — new branch from the current one.
- `d` — delete a branch (`-d` semantics; prompts to force if needed).
- `M` — merge selected branch into the current one; `r` — rebase current onto it.
- `f` — fast-forward the selected branch to its upstream.

## History & rewriting

In the **Commits** panel:

- `Enter` — view a commit's files/diff.
- `r` — reword a commit message; `e` — start an interactive rebase from here.
- `s` — squash the selected commit into the one below; `f` — fixup.
- `d` — drop a commit; `p` — pick. Move commits with the reorder keys shown in `?`.

Interactive rebase in lazygit avoids hand-editing the todo list — you select
the action per commit. Great for tidying a vibe-coding branch before a PR.

## Stash & remotes

- Files panel `s` — stash all changes; **Stash** panel `Space`/`g` — pop/apply.
- Push/pull from the top bar: `P` — push, `p` — pull (respects your
  `pull.rebase` config); lazygit shows ahead/behind counts so you know when to
  push.

## When to drop back to the CLI

- Anything scripted or agent-driven (the CLI is deterministic; TUIs aren't).
- `git worktree` management — use the CLI (see
  [`worktrees-parallel-agents.md`](worktrees-parallel-agents.md)).
- Release tagging and pushes with `--follow-tags` — clearer as explicit
  commands (see [`versioning-and-releases.md`](versioning-and-releases.md)).

Treat lazygit as scaffolding: keep it while you learn the mental model, lean on
the plain commands for anything you'd want to automate or explain.
