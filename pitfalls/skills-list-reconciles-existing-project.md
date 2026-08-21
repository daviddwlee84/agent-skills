# `npx skills add --list` rewrites `skills-lock.json` and `.agents/skills` in an existing project

## Symptom

Running what appears to be a read-only inventory command from an initialized
project:

```bash
npx skills@latest add daviddwlee84/agent-skills/skills --list
```

prints:

```text
Agent detected — installing non-interactively
...
Found 61 skills
Available Skills
```

but also changes project state. With `skills@1.5.23`, the observed diff included:

- a 300-line rewrite of `skills-lock.json`;
- deletion of existing `.agents/skills/*` discovery symlinks;
- creation of directories for nearly every available skill;
- executable mode changes from `100755` to `100644` inside an existing
  installed skill.

The command still exited 0 and displayed the expected available-skill list, so
its stdout did not reveal that reconciliation had occurred.

## Root cause

`--list` is not reliably side-effect-free when `skills add` runs inside an
existing agent-managed project. In the observed Claude Code session, the CLI
detected the active agent and entered its non-interactive project path before
listing the source. That path reconciled existing skill state even though
`--list` was present.

The exact upstream branch that performs the reconciliation has not yet been
isolated. The behavioral boundary is reproducible: the same `skills@1.5.23`
command run from an empty temporary directory listed all 61 skills and created
no project files, while running it at this repository root rewrote the tracked
skill state described above.

## Workaround

Run source inventory from a disposable working directory, not from the project
you are maintaining:

```bash
scratch="$(mktemp -d)"
(cd "$scratch" && npx skills@latest add daviddwlee84/agent-skills/skills --list)
rm -rf "$scratch"
```

This changes only the process working directory; the source argument and
manifest grouping are unchanged. If the CLI later starts writing scratch state,
the final removal still contains it outside the real project.

If an agent already ran `--list` in the project, inspect `git status` before
restoring anything. When the pre-command tree was known clean, restore only the
CLI-generated paths:

```bash
git restore -- .agents/skills skills-lock.json
git clean -fd -- .agents/skills
```

Do not use the cleanup commands blindly in a project that had pre-existing
untracked skills; `git clean` would remove them.

## Prevention

- Treat every `skills add` invocation as potentially mutating, including
  `--list`.
- Agents should run availability checks in a temporary directory and compare
  `git status --short` before and after any install/update smoke.
- Keep native loader smoke tests isolated with tool-specific state directories;
  `scripts/smoke-claude-marketplace.sh` applies the same invariant to Claude
  Code through temporary `HOME` and `CLAUDE_CONFIG_DIR`.
- Preserve the explicit `/skills` source subpath in the scratch command so the
  grouped marketplace manifest is still exercised.

## Where this was hit

During the 2026-08-21 native Claude/Codex packaging comparison, the final
`npx skills@latest add daviddwlee84/agent-skills/skills --list` verification ran
from this repository root under Claude Code 2.1.235. npm resolved
`skills@1.5.23`; the command listed 61 skills but mutated the tracked dogfooding
links, vendored script modes, and `skills-lock.json`. The changes were identified
by final diff-scope review, then removed. A repeat from a temporary empty
working directory produced the same 61-skill list with no project-state files.
