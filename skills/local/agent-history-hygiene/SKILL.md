---
name: agent-history-hygiene
description: Commit SpecStory transcripts and Claude/Cursor/OpenCode/Codex plans with feature diffs, derive staged `AI-Assisted-By` plus transcript/plan trailers, prevent secret leaks, and ignore SpecStory machine-local state. Use when asked to commit/save/stage agent sessions, record cross-harness provenance, bootstrap pre-commit, fix `.specstory/statistics.json` churn, scrub a transcript, or remediate accidental secret commits/pushes with rotate-first discipline.
---

# agent-history-hygiene

Keep agent chat transcripts and plan files committed together with the
code they produced, without leaking secrets. Pairs with the
`redact-agent-secrets` + `gitleaks` pre-commit hooks the skill installs.

Surfaces, separated by purpose:

| Surface                          | Question it answers                                          |
|----------------------------------|--------------------------------------------------------------|
| `find-session.sh`                | "Which transcript / plan file is *my* current session?"      |
| `stage-agent-artifacts.sh`       | "Which agent files belong in the next commit?"               |
| `agent-commit-metadata.sh`       | "Which harness/model + artifact trailers belong in it?"      |
| `bootstrap-project.sh`           | "How do I get pre-commit + gitleaks + redactor into a repo?" |
| `scan-staged.sh`                 | "Is there a leaked secret in what I'm about to commit?"      |
| `probe-specstory-redaction.py`   | "What does SpecStory already redact, so we don't redo it?"   |
| `references/remediation.md`      | "I already pushed a secret — now what?"                      |

## Core invariants

1. **Agent transcripts and plan files are committed alongside the diff
   that produced them.** Never add them to `.gitignore`. An agent that
   drops these from a commit has broken the user's review trail.
2. **SpecStory state is not review history.** Precisely ignore
   `.specstory/.project.json` (machine/path-derived identity) and
   `.specstory/statistics.json` (regenerable statistics), but never ignore
   `.specstory/` or `.specstory/history/` as a whole.
3. **Rotate at the provider before any git rewrite.** The only act
   that revokes a leaked credential is rotation. History rewriting
   scrubs bytes on one clone and leaves them on every other.
4. **`git push --force` against a shared branch is never the fix for a
   leak.** At best it's useless; at worst it destroys teammate work and
   silently re-introduces the secret when someone merges their old
   history back.
4. **Provenance is derived from the staged snapshot.** Never point a commit
   trailer at an unstaged transcript/plan, and never guess an unknown model.
5. **Nothing this skill ships may trip a downstream scanner.** `npx skills
   add` installs this whole directory — `tests/` and `fixtures/` included —
   into the consumer's repo under `.agents/skills/`, inside their own scan
   scope. `detect-private-key` honours no allowlist marker, so a literal
   `BEGIN … PRIVATE KEY` here fails *their* commit with nothing they can edit
   to stop it. Build key headers at runtime (`pem_header()` in
   `tests/conftest.py`) or use a `__SYNTHETIC_PEM_*__` placeholder; never
   answer this with a wider `exclude:`. Enforced by
   `tests/test_shipped_file_hygiene.py`.

## When to use this skill

Use it when the user (or you) surface any of:

- "Commit my chat" / "save the specstory session" / "include the plan
  file in this commit" / "把 plan 跟 specstory 一起 commit 進去".
- You see dirty `.specstory/history/*.md`, `.claude/plans/*.md`,
  `.cursor/plans/*.md`, or any other configured agent artifact during
  `git status` and you're about to commit a feature.
- You see recurring `.specstory/.project.json` or
  `.specstory/statistics.json` churn, especially across machines.
- "Scrub this transcript" / "redact my key" / "gitleaks flagged my
  chat history".
- "Set up pre-commit for this repo" / "I'm starting a new project — how
  do I get the hook stack?" / "bootstrap secret scanning here".
- "I pushed a `.env`" / "a secret went to main" / "do I need to force
  push?" — the agent must steer to `references/remediation.md` and
  stop the user from force-pushing reflexively.

## When NOT to use

- The user explicitly wants agent transcripts **excluded** from the
  repo. Respect that; suggest a one-liner `.gitignore` addition and
  skip this skill entirely.
- The leak is already on a shared `main`/release branch. Do **not**
  offer to rewrite history — jump to `references/remediation.md` §5.
- The project genuinely has no agent session (no `.specstory/`, no
  `.claude/plans/`, etc.). Nothing to stage.
- Single-file, single-commit hygiene that the agent handles without any
  script (e.g., adding a missing trailing newline).

## Integration with existing infrastructure

This skill sits **on top of** any chezmoi-managed stack the user
already has. It does not duplicate:

- **chezmoi's global `core.hooksPath`** (`~/.config/git/hooks/pre-commit`)
  — that wrapper runs the repo's `.pre-commit-config.yaml` and then
  optionally `gitleaks git --staged`. The skill bootstraps the repo-level
  config the wrapper expects to find.
- **chezmoi's `.gitleaks.toml`** — the user's config already carries
  curated rules for common API keys (OpenAI, Anthropic, Supabase,
  Linear, WakaTime, Cursor, HuggingFace, Notion, Tailscale, Clash /
  V2Ray tokens). The skill's `assets/gitleaks.toml.template` ships the
  same rule IDs so `.gitleaksignore` / allowlist tweaks stay portable.
- **the pinned `redact-agent-secrets` hook** — the redactor ships as a
  pinned pre-commit hook from this repo
  (`.pre-commit-hooks.yaml`), so every consuming repo gets fixes via
  `pre-commit autoupdate` instead of a vendored copy that drifts. Details
  in [`references/pre-commit-redaction-stack.md`](references/pre-commit-redaction-stack.md).

What this skill **adds**:

- Agent-facing discipline (this `SKILL.md` + `references/remediation.md`).
- A single-command project bootstrap (`bootstrap-project.sh`) for repos
  without chezmoi or where the user wants the stack in one go.
- Session-discovery heuristics (`find-session.sh`) for the "find my
  current transcript among many" problem.
- An exit-code wrapper (`scan-staged.sh`) agents can branch on before
  committing.

## Workflow A: commit-time hygiene

Default flow when the agent is about to commit feature changes plus
chat/plan artifacts.

```bash
# 1. Make sure the agent knows which session is "ours" — mostly
#    relevant when multiple Claude/SpecStory sessions run in the repo.
bash skills/local/agent-history-hygiene/scripts/find-session.sh

# 2. Stage code the usual way, then auto-add agent artifacts.
git add path/to/feature/file.ts
bash skills/local/agent-history-hygiene/scripts/stage-agent-artifacts.sh
# Use --session-only if you want ONLY the current SpecStory + newest plan;
# default stages every dirty *.md in every configured agent dir.

# 3. Generate the canonical FINAL trailer block from staged artifacts.
bash skills/local/agent-history-hygiene/scripts/agent-commit-metadata.sh

# 4. Belt-and-suspenders secret scan before commit. Exit 0 = clean.
bash skills/local/agent-history-hygiene/scripts/scan-staged.sh || {
  # Exit 10/20: leaks found. Jump to references/remediation.md.
  echo "Leaks detected — see references/remediation.md before committing." >&2
  exit 1
}

# 5. Append that block after any native attribution, validate with the
#    git-workflow companion, then commit. pre-commit re-runs redaction/gitleaks.
bash skills/local/git-workflow/scripts/check-commit-msg.sh \
  --agentic --staged --file /path/to/commit-message.txt
git commit -F /path/to/commit-message.txt
```

## Workflow B: bootstrap a new project

For repos that don't yet have `.pre-commit-config.yaml` / `.gitleaks.toml`
installed. Runs once per repo.

```bash
cd /path/to/new/project
bash skills/local/agent-history-hygiene/scripts/bootstrap-project.sh \
  --install-hook            # optional: auto-stage on every commit

# Verify: shake out any existing issues in the working tree.
pre-commit run --all-files
```

What `bootstrap-project.sh` does:

1. Drops `.pre-commit-config.yaml` + `.gitleaks.toml` into the repo
   (skips if already present unless `--force`). The redactor is a pinned
   remote hook (`repo: …/agent-skills`, `rev: ahh-v1.1.0`), **not** a
   vendored `scripts/redact_secrets.py` — so `pre-commit autoupdate`
   keeps it current everywhere.
2. Creates or merges `.specstory/.gitignore` with only these anchored rules:

   ```gitignore
   /.project.json
   /statistics.json
   ```

   This keeps machine-local identity and generated statistics out of Git
   without hiding `.specstory/history/`. If either state file is already
   tracked, bootstrap warns because ignore rules do not affect tracked files;
   re-run with `--untrack-specstory-state` to apply `git rm --cached` while
   keeping the local files on disk. Use `--dry-run` to preview it.
3. Runs `pre-commit install` (or `uvx pre-commit@4 install` if
   pre-commit isn't on `PATH`).
4. Audits `.gitignore` / `.git/info/exclude` for patterns that would
   silently hide an agent artifact dir — warns without editing.
5. Checks `~/.claude/settings.json` for `plansDirectory`; prints the
   one-line patch if missing.
6. With `--install-hook`: writes a `prepare-commit-msg` hook that calls
   `stage-agent-artifacts.sh --session-only --allow-empty` so every
   `git commit` auto-attaches the current session file. If `core.hooksPath` is
   configured, bootstrap fails before writing anything: `.git/hooks/` would be
   inactive, so the user must integrate the hook into the configured directory
   or unset that override for the repo.

Migrating a repo off the **old vendored layout** (a committed
`scripts/redact_secrets.py` + a `- repo: local` redact hook):

```bash
bash skills/local/agent-history-hygiene/scripts/bootstrap-project.sh --migrate
```

removes the vendored script and rewrites the local hook into the pinned
remote hook, leaving your other hooks and `.gitleaks.toml` untouched
(idempotent; safe to re-run).

## Workflow C: post-leak remediation

When `scan-staged.sh` reports exit `10`/`20`, or the user says "I
committed / pushed a secret":

1. **STOP** the user from running `git push --force` reflexively.
2. Read `references/remediation.md` end-to-end.
3. Walk the user through **step 1 (rotate)** regardless of blast
   radius. Only after rotation does the question of scrubbing history
   become worth discussing.
4. Use the decision tree in the runbook to pick the right git action.

## Gotchas

- **`.gitignore` does not retroactively untrack files.** SpecStory's own
  nested ignore historically covered `.project.json` but not the later-added
  `statistics.json`, and either file may already be committed. Adding the two
  precise rules stops new files only. Run bootstrap with
  `--untrack-specstory-state` to stage their removal from Git while preserving
  both local files. Never compensate with `.specstory/` or
  `.specstory/history/` in an ignore file; that discards the review trail.
- **SpecStory >= 2.4.0 already redacts on write — plan around it, not
  against it.** Since
  [PR #235](https://github.com/specstoryai/getspecstory/pull/235) shipped in
  v2.4.0 (2026-07-20), the CLI redacts secrets via the
  [Betterleaks](https://github.com/betterleaks/betterleaks) ruleset **by
  default**, covering both local markdown and cloud sync, writing
  `[REDACTED:<rule-id>]`. Measured coverage is 36 of 54 class/context pairs;
  15 are ours alone (every webhook rule, plus every custom key in prose
  context — betterleaks catches many classes only in `KEY=value` form via its
  entropy-based `generic-api-key` rule). So: **keep this layer, but never
  rewrite what SpecStory already cleaned.** `redact_secrets.py` writes the
  same `[REDACTED:<rule-id>]` sentinel and `.gitleaks.toml` allowlists it, so
  a cleaned transcript is left untouched and pre-commit stops demanding a
  re-`git add`. Full matrix + knobs in
  [`references/specstory-native-redaction.md`](references/specstory-native-redaction.md).
  Only `[redaction] enabled` is configurable upstream — the PR's
  `extra_patterns` did not survive the Betterleaks rewrite, so repo-specific
  rules stay our job. For SpecStory older than 2.4.0 (or with redaction
  disabled), run `redact_secrets.py --fix --legacy`.
- **`plansDirectory` project-level sometimes ignored.** Claude Code
  issue [#19537](https://github.com/anthropics/claude-code/issues/19537)
  reports project-level `plansDirectory` being ignored in some
  versions. After running a `/plan`, verify the file actually landed
  where you expected before relying on `stage-agent-artifacts.sh`
  picking it up. User-level config (`~/.claude/settings.json` with
  `"plansDirectory": "./.claude/plans"`) is the recommended default.
- **`gitleaks protect` is deprecated.** Since v8.19.0 use
  `gitleaks git --staged --redact` (pre-commit) and
  `gitleaks dir <path>` (working directory). The older commands still
  work but emit a deprecation notice. This skill uses the modern
  syntax everywhere.
- **`pre-commit install` is per-clone.** Each teammate must run
  `pre-commit install` in their own clone for hooks to fire. CI cannot
  be trusted as the single gate — it's second-chance, not last-chance.
- **Transcript files can be huge.** A long SpecStory session can exceed
  2 MB. The template bumps `check-added-large-files` to `--maxkb=2048`
  to avoid false positives, but a very long session can still overflow.
  If you hit the limit, rotate sessions (`specstory run claude`
  creates a fresh file) instead of raising the cap further.
- **Session-UUID divergence between SpecStory CLI and VS Code
  extension.** The extension autosaves into `.specstory/history/`
  continuously; the CLI (`specstory run claude`) creates one file per
  invocation. If both are active you can end up with two transcripts
  for what feels like "one session" — mtime-newest wins in
  `find-session.sh`.
- **Global `core.hooksPath` means bare repos aren't protected.** The
  chezmoi setup's global hook runs `.pre-commit-config.yaml` IF it
  exists — so a repo without `.pre-commit-config.yaml` has no
  protection. Run `bootstrap-project.sh` before the first commit with
  agent artifacts, not after.
- **`--install-hook` cannot bypass `core.hooksPath`.** Git reads hooks from the
  configured directory instead of `.git/hooks/`; writing a repo-local
  `prepare-commit-msg` there would silently do nothing. Bootstrap now exits 6
  before creating files and prints the two valid remedies. It never edits a
  user's global hook directory on their behalf.
- **Active SpecStory writer can defeat the redact loop.** The standard
  `git add → git commit → pre-commit auto-fixes → re-stage → re-commit`
  flow assumes the file is **quiescent** during the commit. SpecStory's
  `specstory_*_watch` daemon tails the agent transcript continuously,
  so if the chat captured `ps -axo args`-style output that contained an
  unrelated daemon's secret in argv (e.g. SpecStory's own
  `--cloud-token …` flag), every diagnostic command (`grep`, `sed -n
  '<line>p'`, `cat | head | tail`) prints the secret again, SpecStory
  appends it to the transcript, and the redact-then-restage cycle
  never converges. Symptom: pre-commit says "Successfully redacted N
  file(s)" but `gitleaks-system` immediately fails on the same line,
  re-running `git add && git commit` doesn't help, and `grep -c
  '<secret-prefix>' file` shows the count *increasing* over commit
  attempts. **Workaround**: a single atomic
  `python3 -c "<in-place re.sub>" && git add <file> && git commit -m
  "..."` pipeline so the index is frozen before any new specstory write
  lands. **Don't** print, grep, or diff the secret line during the
  recovery — every print echoes back into the transcript. Diagnose with
  `lsof <file>` (looking for `specstory_*` writers) instead. See
  `pitfalls/redact-secrets-loop-with-active-specstory-writer.md` in
  upstream chezmoi for the full debugging trail.
  **Fixed sub-case:** the *bare-phrase* variant of this loop — where the
  redactor's own `PRIVATE KEY` substring match kept flagging prose that
  merely *discusses* private keys (this skill's docs, or a chat about
  redaction) with **no real secret present** — no longer happens.
  `redact_secrets.py` now scopes to key *headers* (the
  `detect-private-key` BLACKLIST), so prose mentions are ignored and
  converge immediately. The atomic-commit workaround above is still
  needed for the harder case: a **real** secret an active writer keeps
  re-appending. When only the substring redactor (`redact-agent-secrets`)
  trips while `gitleaks` + `detect-private-key` pass, it's the false
  positive — verify with `gitleaks git --staged` and, if clean, commit
  with `SKIP=redact-agent-secrets` (keeps the real gates active).

## Available scripts

- **`scripts/find-session.sh [--format=specstory|claude|both] [--json]`**
  Discover the current agent session files for `$PWD`. TSV default,
  `--json` for structured callers. Never exits non-zero (always 0,
  empty fields signal absence).

- **`scripts/stage-agent-artifacts.sh [--session-only] [--include-all-plans] [--dry-run] [--allow-empty]`**
  `git add` the right agent artifacts before the next commit.
  `--session-only` stages only the current SpecStory + newest plan;
  default stages every dirty `*.md` in every configured artifact dir.
  Refuses to run if there are no code changes (prevents "commit just
  transcript"); override with `--allow-empty`.

- **`scripts/agent-commit-metadata.sh [--harness NAME --model NAME] [--format trailers|json]`**
  Read staged SpecStory/plan artifacts and emit deduplicated
  `AI-Assisted-By`, `Agent-Transcript`, and `Agent-Plan` values. Parses the
  staged blob rather than a concurrently-changing working-tree transcript;
  requires explicit harness+model overrides when it cannot prove them.

- **`scripts/scan-staged.sh [--redact] [--verbose]`**
  Run `gitleaks git --staged` with agent-friendly exit codes
  (0 clean / 10 redacted / 20 leaks / 30 gitleaks missing). JSON lines
  on stdout, prose diagnostics on stderr.

- **`scripts/probe-specstory-redaction.py [--json] [--keep] [--dry-run]`**
  Measure which secret classes SpecStory's native redaction covers, by
  synthesizing a Claude Code session and rendering it twice (with and without
  `--no-redact-secrets`). Prints a coverage matrix and the residual set our
  layer must still handle. Exit 30 when specstory isn't installed.

- **`scripts/bootstrap-project.sh [--from-chezmoi] [--migrate] [--install-hook] [--untrack-specstory-state] [--force] [--dry-run]`**
  Install `.pre-commit-config.yaml` + `.gitleaks.toml` into the current
  repo, merge precise SpecStory state ignores, wire the hook to the installed
  skill's redactor, then run `pre-commit install`. Audits
  `.gitignore` and `~/.claude/settings.json` for misconfigurations
  without hiding transcript directories. Already-tracked state is only
  untracked with the explicit flag; `--dry-run` previews that index change.
  `--install-hook` exits 6 when `core.hooksPath` would make the repo-local
  hook inert.

## Bundled assets

- `assets/artifact-dirs.txt` — the canonical list of agent artifact
  directories (SpecStory, Claude plans, Cursor plans + rules, OpenCode
  plans, Spec-kit, Codex). Consumed by `stage-agent-artifacts.sh` and
  by `bootstrap-project.sh` when rendering the pre-commit `files:`
  regex.
- `assets/pre-commit-config.yaml.template` — minimal
  `.pre-commit-config.yaml` with `redact-agent-secrets` + gitleaks +
  standard hygiene hooks.
- `assets/gitleaks.toml.template` — portable subset of the chezmoi
  `.gitleaks.toml` with custom rule IDs + a path-scoped allowlist for
  agent artifact dirs.
- `assets/redact_secrets.py` — the redactor, published to consuming repos
  as the pinned `redact-agent-secrets` pre-commit hook (root
  `.pre-commit-hooks.yaml`). Writes `[REDACTED:<rule-id>]`, the sentinel
  SpecStory also writes natively; `--legacy` writes the pre-2.4.0
  placeholders instead. Release procedure in
  `references/pre-commit-redaction-stack.md`.

## Reference files

- [`references/transcript-session-discovery.md`](references/transcript-session-discovery.md)
  — SpecStory / Claude session layouts and the `$PWD → slug` algorithm.
  Read when `find-session.sh` returns empty or ambiguous results.
- [`references/pre-commit-redaction-stack.md`](references/pre-commit-redaction-stack.md)
  — three-layer defense (redact → gitleaks → `scan-staged.sh`),
  allowlist design, sync procedure for the bundled redactor. Read
  when tuning rules or debugging unexpected pre-commit failures.
- [`references/specstory-native-redaction.md`](references/specstory-native-redaction.md)
  — what SpecStory >= 2.4.0 redacts on its own, measured per secret class and
  per context, plus the upstream PRs, config knobs, and why our layer is still
  load-bearing. Read before changing anything about redaction placeholders.
- [`references/remediation.md`](references/remediation.md) —
  rotate-first runbook for "I committed / pushed a secret". Read
  **before** any `git filter-repo` / `git push --force` action.

## Tests

The skill ships with a test suite under
[`tests/`](tests/README.md). Run from repo root:

```bash
make test-skill
```

- `test_redact_secrets.py` — pytest for pure redactor functions.
- `test_gitleaks_corpus.py` — golden-corpus fixtures staged in tmp git
  repos, asserting real-key shapes fire and example shapes are
  allowlisted only inside configured artifact dirs.
- `test_scan_staged.sh` — exit-code contract for
  `scripts/scan-staged.sh` (0 / 20 / 30 / 2).
- `test_bootstrap_project.py` — exact SpecStory state ignores, idempotency,
  dry-run, history visibility, and opt-in untracking behavior.
- `test_specstory_coverage.py` — locks in that SpecStory still redacts by
  default and still writes `[REDACTED:<label>]`; skips without the CLI.
- `test_agent_commit_metadata.sh` — staged transcript/model parsing, model
  deduplication, path handling, JSON output, and explicit-override failures.
- `test_shipped_file_hygiene.py` — no shipped file carries a
  `detect-private-key` BLACKLIST substring, and the redactor scrubs all ten
  of them convergently. Runs everywhere; needs no external binary.

The corpus + shell tests skip gracefully when `gitleaks` isn't on
`PATH`. See [`tests/README.md`](tests/README.md) for what each
regression the suite locks in.

## Related skills

- [`git-workflow`](../git-workflow/SKILL.md) — defines and validates the
  English Conventional Commit + canonical provenance contract emitted here.

- [`project-knowledge-harness`](../project-knowledge-harness/SKILL.md)
  — complementary memory harness (TODO.md + backlog/ + pitfalls/) that
  references `.claude/plans/` as "ephemeral agent scratchpads". This
  skill fills the gap: those scratchpads belong in git, not ignored.
