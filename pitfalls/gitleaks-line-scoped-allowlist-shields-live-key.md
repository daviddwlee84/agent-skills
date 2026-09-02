# A `[REDACTED:...]` sentinel hides a live key on the same line

**Symptoms** (grep this section): a real credential inside `.specstory/history/`
or `.claude/plans/` is never reported · `gitleaks git --staged` says
`no leaks found` for a line that visibly contains a live token · the same bytes
DO fire when moved to `src/` · `scan-staged.sh` / `redact_secrets.py
--check-index` exits 0 on a partially redacted line
**First seen**: 2026-09
**Affects**: any repo using this skill's `.gitleaks.toml` with a path-scoped
allowlist at `regexTarget = "line"`
**Status**: fixed; regression-tested by
`tests/test_gitleaks_corpus.py::TestSentinelBesideLiveKey`

## Symptom

A transcript line carrying one already-redacted value and one live value:

```text
OPENAI_API_KEY=[REDACTED:openai-project-key] BACKUP_KEY=sk-proj-<100 live chars>
```

is reported clean inside an agent-artifact directory, while the identical bytes
under `src/` fire `openai-project-key`.

## Root cause

Two independent gitleaks allowlist knobs, and both matter:

- `condition = "AND"` — without it, `paths` and `regexes` are OR'd, so listing
  `paths` blanket-trusts those directories.
- `regexTarget` — `"line"` compares the allowlist regexes against the **whole
  source line**; `"match"` compares them against **the finding's own bytes**.

The path-scoped allowlist tolerated documentation shapes (`example-key`,
`your-api-key-here`, and `\bREDACTED\b`) at `"line"` scope. A line containing a
sentinel therefore matched `\bREDACTED\b`, and the entire line — including any
live credential sharing it — was allowlisted.

Transcripts produce exactly this shape whenever a tool echoes a multi-value line
(`cat .env`, an error quoting several variables) and only some values were
redactable, so it is the normal case rather than a corner case.

## Workaround / fix

Keep **both** on the path-scoped allowlist:

```toml
[[allowlists]]
  condition   = "AND"     # else `paths` blanket-trusts the directory
  paths       = [ ... ]
  regexTarget = "match"   # else a tolerated word covers its line-mates
  regexes     = [ ... ]
```

`"match"` still suppresses an inert `[REDACTED:<rule>]` placeholder, because the
finding's own bytes are the placeholder. It stops suppressing its neighbours.

## Prevention

Any allowlist entry whose purpose is "tolerate this *token*" must be
`regexTarget = "match"`. Reserve `"line"` for entries that genuinely mean
"trust this entire line". When changing allowlist scope, verify with a fixture
that puts a live secret and a tolerated placeholder on one line — a config that
only ever sees clean or only-dirty lines cannot distinguish the two settings.

Verify with `gitleaks git --staged` (what pre-commit and the finalizer run), not
`gitleaks detect --no-git --source <file>`: the latter resolves paths relative to
`--source`, so path-scoped allowlists do not match and results are misleading.
