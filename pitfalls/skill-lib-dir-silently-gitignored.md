# New skill `scripts/lib/` never shows up in `git status`

## Symptom

A new helper directory under a skill (e.g.
`skills/local/<skill>/scripts/lib/`) works locally, every test passes, but
`git status --short` lists the sibling scripts and **not** the directory —
no `?? .../lib/` line, no error. Committing would ship scripts that
`source` files missing from the published repo:

```
$ git check-ignore -v skills/local/project-knowledge-harness/scripts/lib/td-bridge.sh
.gitignore:17:lib/	skills/local/project-knowledge-harness/scripts/lib/td-bridge.sh
```

## Root cause

The repo `.gitignore` starts from GitHub's Python template, which ignores
`lib/` (and `build/`, `dist/`, `env/`, …) at **any depth**. Installed skills
are fetched from the git tree, so an ignored dir is silently absent downstream.

## Workaround

Name helper dirs so the template doesn't match them — `_lib/` is what
`project-knowledge-harness` uses — or add a negation such as
`!skills/**/lib/`. Renaming is more robust: downstream repos that vendor the
skill may carry the same Python template.

## Prevention

After adding any new directory under `skills/`, run
`git status --short --untracked-files=all <skill dir>` (or
`git check-ignore -v <new file>`) before committing.
