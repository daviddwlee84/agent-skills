# Plan: `agent-history-hygiene` skill

## Context

The user tracks agent chat history with **SpecStory** (`.specstory/history/*.md`) and keeps Claude Code plan files in-repo via `plansDirectory: "./.claude/plans"`, committing both alongside the feature diff that produced them. The workflow already works for the user locally — chezmoi carries a `redact-agent-secrets` pre-commit hook, a comprehensive `.gitleaks.toml`, and a global `core.hooksPath` wrapper.

Three gaps remain:

1. **Default LLM behavior drifts against the user's intent.** Agents treat `.specstory/history/*.md` and `.claude/plans/*.md` as auto-generated artifacts and exclude them from commits unless told otherwise. There's no skill capturing the "always commit these, and find *your* session among many" rule.
2. **The infrastructure doesn't transplant cleanly.** A fresh repo without chezmoi has no pre-commit config, no gitleaks rules, and no `plansDirectory` — the user wants a single `bootstrap-project.sh` instead of per-repo drudgery.
3. **Post-leak discipline isn't captured.** When secrets slip into a transcript the user wants the skill to enforce rotate-first, rewrite-last — explicitly steering agents away from reflexive `git push --force` to "scrub" a shared branch.

This plan creates `skills/local/agent-history-hygiene/` as the canonical surface. Chezmoi changes are intentionally minimal — the existing stack is 90% there; the skill adds the glue and the agent-facing discipline.

## Recommended approach

Create a single local skill with 4 scripts, 3 reference docs, and 4 assets. Make one small chezmoi addition (SpecStory/plans allowlist) and one small chezmoi fix (deprecated `gitleaks protect` → `gitleaks git --staged`).

### Decisions locked in (from user answers)

- **Name**: `agent-history-hygiene`
- **Artifact scope**: `.specstory/history/`, `.claude/plans/`, `.cursor/plans/`, `.cursor/rules/`, `.opencode/plans/`, `.specify/`, `.codex/` — plus a configurable list (`assets/artifact-dirs.txt`) so new agent dirs get picked up without editing scripts.
- **Auto-stage**: ship `stage-agent-artifacts.sh` agent-invoked by default; provide `bootstrap-project.sh --install-hook` for optional git `prepare-commit-msg` auto-stage.
- **Redactor**: bundle `redact_secrets.py` under `assets/`. Document the chezmoi version as upstream-of-record; sync procedure spelled out in `references/pre-commit-redaction-stack.md`.

### 1. Skill structure

```
skills/local/agent-history-hygiene/
├── SKILL.md
├── scripts/
│   ├── find-session.sh           # locate current SpecStory + Claude session for $PWD
│   ├── stage-agent-artifacts.sh  # git-add the right artifacts before commit
│   ├── bootstrap-project.sh      # install pre-commit + gitleaks + hook into a new repo
│   └── scan-staged.sh            # run `gitleaks git --staged --redact` with agent-friendly exit codes
├── references/
│   ├── transcript-session-discovery.md
│   ├── pre-commit-redaction-stack.md
│   └── remediation.md
└── assets/
    ├── pre-commit-config.yaml.template
    ├── gitleaks.toml.template
    ├── redact_secrets.py         # bundled copy (upstream = chezmoi)
    └── artifact-dirs.txt         # editable allowlist of agent artifact directories
```

### 2. `SKILL.md` outline

Frontmatter `description` — pushy, trigger-dense, ~55 words. Mentions: "commit my chat", "save specstory session", "stage the plan file", "scrub transcript", "my .env leaked in chat", "bootstrap pre-commit", plus the passive trigger "you see untracked `.specstory/history/` during `git status`".

Sections (in order):

1. **Core invariants** — three rules: commit transcripts + plans alongside diff; rotate-at-provider *before* any git rewrite; never `--force` against a shared branch to hide a leak.
2. **When to use / When NOT to use** — concrete phrases + the "they explicitly want transcripts excluded" exception.
3. **Integration with existing infrastructure** — points at chezmoi's `redact-agent-secrets` + `.gitleaks.toml` + global `core.hooksPath`; explains what this skill adds (invocation + bootstrap + agent-facing discipline) vs what chezmoi owns (rules + redactor source-of-truth).
4. **Workflow A: commit-time hygiene** — `find-session.sh` → `stage-agent-artifacts.sh` → `scan-staged.sh` → `git commit`.
5. **Workflow B: bootstrap a new project** — `bootstrap-project.sh` (optionally `--install-hook`, `--from-chezmoi`) → audit `.gitignore` won't silently hide artifacts.
6. **Workflow C: post-leak remediation** — rotate-at-provider checklist → branch-shared-ness assessment → redact + new commit (preferred) → history rewrite only as last resort + only on unshared branches.
7. **Gotchas** — six items (plansDirectory issue #19537, `gitleaks protect` deprecation, `pre-commit install` is per-clone, transcript file size, session-UUID divergence between SpecStory CLI and VS Code extension, global `hooksPath` means bare repos aren't protected).
8. **Available scripts** — signature + one-line purpose.
9. **Reference files** — lazy-load hints ("read `remediation.md` if gitleaks finds a real leak").

Target ~350 lines. Anything longer moves to `references/`.

### 3. Scripts (4, all bash, `set -euo pipefail`, `--help`, `--dry-run` where applicable)

**`find-session.sh [--json] [--format=specstory|claude|both]`**
- Claude UUID = newest `*.jsonl` in `~/.claude/projects/<cwd-slug>/` (slug = `$PWD` with `/` → `-`).
- SpecStory path = newest `*.md` in `$PWD/.specstory/history/`.
- Output TSV by default; `--json` for structured callers. Never fails the pipeline — prints empty rows + stderr diagnostic if nothing found.

**`stage-agent-artifacts.sh [--dry-run] [--include-all-plans] [--session-only] [--dirs-file PATH]`**
- Reads artifact dirs from `assets/artifact-dirs.txt` (or `--dirs-file`).
- Default: stages (a) the current SpecStory file from `find-session.sh`; (b) all unstaged `.md` files under the configured agent dirs; (c) respects `.gitignore` — warns if an artifact dir is silently ignored.
- `--session-only`: just the current SpecStory file + current plan file.
- Refuses to run if HEAD has no code changes + no dirty artifacts (prevents the "commit just the transcript" anti-pattern).

**`bootstrap-project.sh [--from-chezmoi] [--install-hook] [--force] [--dry-run]`**
- Actions:
  1. Copy `assets/pre-commit-config.yaml.template` → `.pre-commit-config.yaml` (skip if present unless `--force`).
  2. Copy `assets/gitleaks.toml.template` → `.gitleaks.toml` (same behavior).
  3. Copy `assets/redact_secrets.py` → `scripts/redact_secrets.py` (or `--from-chezmoi` symlinks to chezmoi source).
  4. `uvx pre-commit@4 install` (pinned, hermetic).
  5. `--install-hook` only: also write a `prepare-commit-msg` hook that calls `stage-agent-artifacts.sh --session-only` so every commit auto-attaches the current session.
  6. Audit `.gitignore` and `.git/info/exclude` — warn (don't edit) if any configured artifact dir matches an ignore pattern.
  7. Verify `~/.claude/settings.json` has `plansDirectory: "./.claude/plans"`; if not, print the exact JSON patch (don't silently edit).

**`scan-staged.sh [--redact] [--no-redact] [--verbose]`**
- Uses `gitleaks git --staged --redact` (current syntax, not deprecated `protect`).
- Exit codes: `0` = clean, `10` = leaks + redacted, `20` = leaks + no-redact, `30` = gitleaks missing (prints install hint).
- JSON-lines findings to stdout; prose to stderr.

### 4. Reference files (3)

- **`references/transcript-session-discovery.md`** — SpecStory session-UUID conventions (CLI `specstory sync claude -s <uuid>` vs VS Code extension autosave), the `~/.claude/projects/<slug>/*.jsonl` Claude Code internal format, and the `$PWD` → slug algorithm. Load when `find-session.sh` is empty/ambiguous.
- **`references/pre-commit-redaction-stack.md`** — layered defense explained: chezmoi's `redact-agent-secrets` → `gitleaks-system` → `scan-staged.sh` as belt-and-suspenders. Documents `.gitleaksignore`, inline `# gitleaks:allow` pragmas, and the sync procedure for the bundled `redact_secrets.py` (chezmoi is upstream; when chezmoi version drifts, run `cp ~/.local/share/chezmoi/scripts/redact_secrets.py skills/local/agent-history-hygiene/assets/redact_secrets.py` + review diff + commit).
- **`references/remediation.md`** — the rotate-first runbook: (1) identify provider → rotate in console; (2) assess blast radius (pushed? which branches?); (3) if unshared local → amend or `reset --soft HEAD~ && redact && recommit`; (4) if shared → `git filter-repo --invert-paths --path <file>` + force-with-lease on feature branch only + coordinate teammate re-clones; (5) audit downstream clones and CI caches. Load after `scan-staged.sh` finds a real leak or the user says "I already pushed".

### 5. Assets (4)

- **`assets/pre-commit-config.yaml.template`** — minimal `.pre-commit-config.yaml` with `redact-agent-secrets` local hook + `gitleaks` hook. Uses `gitleaks git --staged --redact`. Artifact-dir regex sourced from `artifact-dirs.txt` at bootstrap time.
- **`assets/gitleaks.toml.template`** — subset of chezmoi `.gitleaks.toml`: custom rules for OpenAI/Anthropic/WakaTime/Cursor/HuggingFace/Supabase/Linear/Tailscale/Notion, plus new `[[allowlists]]` block for `.specstory/history/**` and plan dirs whitelisting demo-key shapes (`sk-XXX…`, `REDACTED`, `example-key`).
- **`assets/redact_secrets.py`** — bundled copy of chezmoi version with PEP 723 header, `--fix`, `--check`. Chezmoi version is upstream-of-record; sync doc in `references/pre-commit-redaction-stack.md`.
- **`assets/artifact-dirs.txt`** — one directory per line: `.specstory/history/`, `.claude/plans/`, `.cursor/plans/`, `.cursor/rules/`, `.opencode/plans/`, `.specify/`, `.codex/`. Consumed by `stage-agent-artifacts.sh` and by `bootstrap-project.sh` when rendering `.pre-commit-config.yaml`'s `files:` regex.

### 6. Chezmoi changes (minimal — `/Users/daviddwlee84/.local/share/chezmoi/`)

1. **`.gitleaks.toml`** — add a narrow allowlist for in-transcript example keys across the full agent-dir list:
   ```toml
   [[allowlists]]
   description = "Example/demo keys inside agent transcripts and plan files"
   paths = [
     '''\.specstory/history/.*\.md$''',
     '''\.claude/plans/.*\.md$''',
     '''\.cursor/(plans|rules)/.*\.md$''',
     '''\.opencode/plans/.*\.md$''',
     '''\.specify/.*\.md$''',
     '''\.codex/.*\.md$''',
   ]
   regexTarget = "line"
   regexes = ['''example[-_]?(key|token|secret)''', '''REDACTED''', '''sk-[a-zA-Z0-9]{3,8}\.\.\.''']
   ```
   Reduces false positives when agents discuss key *shapes* in plans/transcripts. Narrow scope (both path and regex must match), so real leaks still trigger.

2. **`dot_config/git/hooks/executable_pre-commit.tmpl`** — swap deprecated `gitleaks protect --staged` → `gitleaks git --staged --redact`. One-line change; identical semantics post-v8.19.0.

3. **`scripts/redact_secrets.py`** — extend the regex that detects "example-shape" lines so the redactor agrees with the new gitleaks allowlist (avoids the case where gitleaks allows a line but redactor still scrubs it). One-line addition to the existing skip-pattern.

Intentionally **not** adding a chezmoi `run_once_` script — per-repo bootstrap is wrong to run globally; `bootstrap-project.sh` is the right entry point and can be invoked on demand.

### 7. Registration

- **`README.md`** — add bullet under `skills/local/` list (after `mlflow-tracking`) linking the new skill.
- **`docs/skills/index.md`** — add row to Local skills table.
- **`mkdocs.yml`** — add `- agent-history-hygiene: skills/agent-history-hygiene.md` under `nav → Skills → Local`.
- **`docs/skills/agent-history-hygiene.md`** — new detail page (follow pattern of `docs/skills/project-knowledge-harness.md`).

## Critical files

**To create:**
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/SKILL.md`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/scripts/find-session.sh`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/scripts/stage-agent-artifacts.sh`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/scripts/bootstrap-project.sh`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/scripts/scan-staged.sh`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/references/{transcript-session-discovery,pre-commit-redaction-stack,remediation}.md`
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/agent-history-hygiene/assets/{pre-commit-config.yaml.template,gitleaks.toml.template,redact_secrets.py,artifact-dirs.txt}`
- `/Volumes/Data/Program/Personal/agent-skills/docs/skills/agent-history-hygiene.md`

**To edit:**
- `/Volumes/Data/Program/Personal/agent-skills/README.md` — add skill bullet
- `/Volumes/Data/Program/Personal/agent-skills/docs/skills/index.md` — add Local-skills row
- `/Volumes/Data/Program/Personal/agent-skills/mkdocs.yml` — nav entry
- `/Users/daviddwlee84/.local/share/chezmoi/.gitleaks.toml` — add agent-dir allowlist
- `/Users/daviddwlee84/.local/share/chezmoi/dot_config/git/hooks/executable_pre-commit.tmpl` — `gitleaks protect` → `gitleaks git --staged`
- `/Users/daviddwlee84/.local/share/chezmoi/scripts/redact_secrets.py` — align example-shape skip pattern with gitleaks allowlist

## Existing utilities to reuse

- `/Volumes/Data/Program/Personal/agent-skills/skills/local/skill-author/scripts/new-skill.sh` — scaffold the skill dir.
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/skill-author/scripts/lint-skill.sh` — validate before PR.
- `/Volumes/Data/Program/Personal/agent-skills/skills/local/skill-author/assets/` — templates (`SKILL.md.template`, `script-bash.template`, `reference.md.template`).
- `/Users/daviddwlee84/.local/share/chezmoi/scripts/redact_secrets.py` — upstream source for the bundled `assets/redact_secrets.py`.
- `/Users/daviddwlee84/.local/share/chezmoi/.pre-commit-config.yaml` — shape the `pre-commit-config.yaml.template` after this (hook ordering, file regex, pinned versions).
- `/Users/daviddwlee84/.local/share/chezmoi/.gitleaks.toml` — subset for `gitleaks.toml.template`.

## Verification

End-to-end test against a throwaway repo (do after implementation):

1. `tmp=$(mktemp -d) && cd "$tmp" && git init && echo hi > README.md && git add . && git commit -m init`
2. Run `bootstrap-project.sh` → confirm `.pre-commit-config.yaml`, `.gitleaks.toml`, `scripts/redact_secrets.py` present; `.git/hooks/pre-commit` installed; no gitignore-audit warnings.
3. `mkdir -p .claude/plans .specstory/history`
4. Write a plan file with a fake key: `printf '# plan\nOPENAI_API_KEY=sk-proj-realish-looking-fake-01234567890\n' > .claude/plans/p1.md`
5. Write a SpecStory transcript with similar content at `.specstory/history/2026-04-24_test.md`.
6. `stage-agent-artifacts.sh --dry-run` → expect both files listed.
7. Edit code: `echo 'change' >> README.md`; `git add README.md`; `stage-agent-artifacts.sh`; `scan-staged.sh` → expect exit `10` (redacted).
8. `git diff --staged` → confirm the `sk-proj-…` value is replaced by `REDACTED`, prose intact.
9. `git commit -m "feat"` → pre-commit passes (already redacted).
10. **Negative test**: insert a real-shape key (`sk-ant-api03-` + 95 chars) into a plan file, no code change → `scan-staged.sh` exit `10` → commit blocked until re-staged.
11. **Allowlist test**: write `# example sk-proj-XXX...` (with literal ellipsis) inside `.specstory/history/*.md` → `scan-staged.sh` exit `0` (allowlist hits).
12. **Session-discovery test**: run `find-session.sh` from a project dir with existing Claude + SpecStory sessions — confirm it returns the correct UUID and .md path.
13. **Remediation drill**: `git reset --soft HEAD~1` after a "bad" commit, redact, recommit; confirm `git reflog` shows no force-push.
14. **Hook test (`--install-hook`)**: bootstrap a repo with `--install-hook`, edit code without manually staging artifacts, `git commit -m x` → confirm `prepare-commit-msg` hook auto-attaches the current session file.
15. **Lint**: `bash skills/local/skill-author/scripts/lint-skill.sh skills/local/agent-history-hygiene` → passes.
16. **Docs build**: `make docs-build` → new page renders, nav entry present.

Chezmoi changes verified by:

- `chezmoi diff` shows only the 3 intended edits.
- `chezmoi apply --dry-run` → clean.
- In a test repo with a `.gitleaks.toml` containing the new allowlist, run gitleaks against a transcript with demo-shape keys → no findings; against a transcript with a real-shape key → finding reported.
