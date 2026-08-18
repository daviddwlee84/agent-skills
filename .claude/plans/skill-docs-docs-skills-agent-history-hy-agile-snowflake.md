# Align `agent-history-hygiene` with SpecStory's native secret redaction

## Context

We hand-redact secrets out of `.specstory/history/*.md` via a pre-commit
hook (`assets/redact_secrets.py --fix`). Upstream shipped the same idea:

| Ref | What |
|---|---|
| [PR #235](https://github.com/specstoryai/getspecstory/pull/235) | `feat(redaction): automatically redact secrets from saved markdown history` — community PR by [@warnes](https://github.com/warnes), merged 2026-07-20 |
| [PR #253](https://github.com/specstoryai/getspecstory/pull/253) | `gofmt` CI-fix fork of #235, closed in favor of #235 |
| **v2.4.0** (2026-07-20) | Released: redaction **on by default**, via the [Betterleaks](https://github.com/betterleaks/betterleaks) ruleset, covering **both** local markdown and cloud sync |
| [#274](https://github.com/specstoryai/getspecstory/issues/274) (open) | Adjacent leak vector: `specstory watch` exposes the cloud auth token in its process cmdline |

Verified against the installed CLI (2.9.0) rather than from the PR text:

- Flag `--no-redact-secrets` exists on `run` / `sync` / `watch`.
- Config is `[redaction] enabled` in `.specstory/cli/config.toml`
  (user-level `~/.specstory/cli/config.toml` overridden by project-level).
- The placeholder format string in the binary is **`[REDACTED:%s]`**.
- **`extra_patterns` did not survive** the Betterleaks rewrite — no
  `extra_patterns` / `GetRedactionExtraPatterns` symbols in 2.9.0. Only
  `enabled` is configurable, so our repo-specific rules have no upstream
  equivalent.

Two problems follow. **(a)** The skill and its docs never mention that
upstream now redacts, so a future agent assumes SpecStory is unprotected.
**(b)** Our hook does duplicate work: every rewrite triggers pre-commit's
"files were modified by this hook", forcing a re-`git add` + re-commit.
The dominant churn source is not real secrets — it is the redactor's bare
`PRIVATE KEY` → `PRIV***KEY` rewrite firing on any *mention* of the
phrase (26 occurrences in this repo's own history). That was added to
appease pre-commit's `detect-private-key`, but that hook's `BLACKLIST`
only matches `BEGIN … PRIVATE KEY` — bare mentions were never a problem.

Outcome: document the upstream feature, measure what Betterleaks actually
covers with a re-runnable probe, align our placeholder shape to
`[REDACTED:<RULE_ID>]` so the two layers are idempotent with each other,
and stop rewriting files for things that were never leaks.

## Phase 0 — Coverage probe (drives Phases 2–3)

New: **`skills/local/agent-history-hygiene/scripts/probe-specstory-redaction.sh`**
(agent-invocable: `--help`, `--json`, `--keep` to retain the temp session,
`--dry-run`). Design:

1. Refuse politely (exit 30) if `specstory` is missing; print
   `specstory --version` and the effective `[redaction] enabled` value.
2. Build a temp project dir and a **synthetic Claude Code session** at
   `~/.claude/projects/<slug>/<uuid>.jsonl` — slug = abs path with `/`→`-`
   per `references/transcript-session-discovery.md`. Minimal line schema
   (`type: user|assistant`, `message.content`, `uuid`, `timestamp`,
   `cwd`, `sessionId`, `version`), which is enough for the claude provider.
3. Run the same session twice from that dir:
   `specstory sync claude -s <uuid> --print --no-cloud-sync --no-stats
   --no-usage-analytics --no-version-check --silent`, once bare and once
   with `--no-redact-secrets` (baseline).
   *Fallback if `--print` turns out to bypass the redaction path:* drop
   `--print` and use `--output-dir <tmp>`, then read the file.
4. Per token class: present in baseline **and** absent (or replaced by
   `[REDACTED:…]`) in the redacted run ⇒ `covered`. Record the literal
   label SpecStory emitted.
5. Run `gitleaks git`/`stdin` with `assets/gitleaks.toml.template` over
   the **redacted** output — anything still firing is exactly what our
   hook must keep handling (the residual set).
6. Emit JSON lines on stdout + a markdown table on stderr; delete the
   temp `~/.claude/projects/<slug>` dir unless `--keep`.

Token catalog — one synthetic token per class, reusing
`tests/fixtures/*.md` where they already exist and extending to every
custom rule in `assets/gitleaks.toml.template`:

- Betterleaks/gitleaks-default overlap: anthropic, openai (`sk-` and
  `sk-proj-`), `github_pat_`/`ghp_`/`gho_`/`ghs_`, `AKIA…`, `AIza…`,
  `gsk_`, slack/stripe/telegram.
- Our custom rules: `cursor-api-key`, `huggingface-token`,
  `supabase-service-pat`, `linear-api-key`, `tailscale-auth-key`,
  `notion-integration-token`, `wakatime-api-key`,
  `discord-webhook-url`, `zapier-webhook-url`, `make-webhook-url`,
  `stripe-webhook-secret`.
- Shape cases: PEM private-key block, a `.env` dump (`KEY=value` block),
  and the `example_shapes.md` negatives (must stay **un**redacted by
  both layers — false-positive check).

Ship the results as **`references/specstory-native-redaction.md`**: the
coverage matrix, the exact `[REDACTED:<LABEL>]` labels observed, the
residual set, and the CLI/config knobs. Add a
`tests/test_specstory_coverage.py` that skips when `specstory` is absent
and asserts the classes we now rely on stay covered.

## Phase 1 — Notes in the skill + docs

- `SKILL.md`: new **Gotchas** bullet — "SpecStory ≥ 2.4.0 already redacts
  on write" (default on, covers cloud sync, Betterleaks ruleset, no
  `extra_patterns`), plus why our layer still exists (older files, other
  artifact dirs, repo-specific rules). Link the new reference file.
- `references/pre-commit-redaction-stack.md`: insert a **Layer 0**
  (SpecStory-native) above Layer 1 in the ASCII stack, and a subsection
  on the shared `[REDACTED:*]` sentinel.
- `docs/skills/agent-history-hygiene.md` **and** `.zh-TW.md` (bilingual,
  per repo convention): a "SpecStory native redaction (v2.4.0+)" section
  carrying the table from Context above, the coverage summary, and a
  pointer to open issue #274.

## Phase 2 — Redactor: align placeholders, stop the churn

`skills/local/agent-history-hygiene/assets/redact_secrets.py`:

1. Add `redaction_placeholder(rule_id)` → `[REDACTED:<rule-id>]`, matching
   SpecStory's `[REDACTED:%s]` shape. `redact_file()` uses it (the
   finding already carries `RuleID`). **Keep** `redact_secret()` as the
   *console-report* helper — `first3...last3` in the terminal is useful
   for identifying which key to rotate; it just stops being what lands in
   the file.
2. PEM blocks → `[REDACTED:private-key]` (still safely outside
   `detect-private-key`'s `BEGIN … PRIVATE KEY` blacklist).
3. **Delete** the bare `PRIVATE KEY` → `PRIV***KEY` literal replacement
   and the surrounding "mention count" reporting. `find_private_key_files`
   reports PEM blocks only.
4. `--legacy` flag restores today's behavior verbatim (truncation +
   bare-mention rewrite) for pre-2.4.0 SpecStory or anyone who disabled
   `[redaction]`.
5. `.gitleaks.toml.template`: extend the global allowlist regexes with
   `\[REDACTED:[A-Za-z0-9_.-]+\]` so neither layer's sentinel can be
   re-flagged, and keep the existing `*_REDACTED*` regex for old files.

Tests to update in `tests/test_redact_secrets.py` (they currently pin the
old strings): `test_replaces_secret_in_place` (`sk-...AAA`),
`test_replaces_pem_block_wholesale`, `test_replaces_bare_mention` — the
last becomes an assertion that a bare mention is **left alone**, with the
legacy behavior covered under `--legacy`. Update the header prose in
`tests/fixtures/private_key.md` to match.

Existing committed history keeps its old `[REDACTED PRIV***KEY BLOCK]`
markers — no backfill rewrite (it would churn every transcript for zero
security gain).

## Phase 3 — Bootstrap runs the script in place, no copy

Per your requirement: a downstream install should execute the script from
`.agents/skills/agent-history-hygiene/`, not a copy under `scripts/`.
Verified this works — `npx skills add` materialises the whole skill dir
(`assets/` included) at `<repo>/.agents/skills/<name>/`, with
`.claude/skills/<name>` symlinked to it.

- `assets/pre-commit-config.yaml.template`: entry becomes a rendered
  placeholder, resolved by `bootstrap-project.sh` in this order —
  `.agents/skills/agent-history-hygiene/assets/redact_secrets.py` →
  `.claude/skills/…` → existing `scripts/redact_secrets.py` (legacy repos)
  → bundled copy only when `--copy-script` is passed.
- Invoke as `python3 <path> --fix`: the PEP 723 block declares
  `dependencies = []`, so this needs no `uv` and no exec bit (which
  `npx skills` installs do not reliably preserve). Document the
  `uv run --script` equivalent.
- `bootstrap-project.sh`: replace the unconditional
  `install_file "scripts/redact_secrets.py"` step with the resolver;
  `--from-chezmoi` keeps symlinking the chezmoi copy; new `--copy-script`
  preserves the old vendored-copy behavior. Update `--help`, the
  `## Workflow B` block in `SKILL.md`, and the "Bundled assets" list.
- `references/pre-commit-redaction-stack.md`: the sync-with-chezmoi
  section now notes the skill copy is the source of truth for the
  `[REDACTED:*]` behavior, so chezmoi should pull *from* here.

## Phase 4 — chezmoi SpecStory config (outside this repo)

Append the verbatim 2.9.0 `[redaction]` block (extracted from the binary's
config template) to
`~/.local/share/chezmoi/private_dot_specstory/private_cli/create_config.toml`,
above `[providers]`, all lines commented so behavior is unchanged:

```toml
[redaction]
# Redact secrets and API keys from saved markdown history and cloud-synced
# session data. (default: true)
# Detection uses the betterleaks ruleset, covering API keys, tokens, private
# keys, and other credentials for many providers.
# enabled = false # equivalent to --no-redact-secrets
```

That file also predates 2.4.0 in other ways; I'll leave the rest alone.
Left untouched unless you say otherwise: porting the modified
`redact_secrets.py` back into chezmoi's `scripts/`.

## Files touched

```
skills/local/agent-history-hygiene/
  SKILL.md                                    # gotcha + workflow B + assets list
  assets/redact_secrets.py                    # placeholders, --legacy, drop bare-mention
  assets/gitleaks.toml.template               # allowlist [REDACTED:*]
  assets/pre-commit-config.yaml.template      # entry -> .agents/skills path
  scripts/bootstrap-project.sh                # resolver + --copy-script
  scripts/probe-specstory-redaction.sh        # NEW
  references/specstory-native-redaction.md    # NEW (probe results)
  references/pre-commit-redaction-stack.md    # Layer 0 + sentinel + sync direction
  tests/test_redact_secrets.py                # retarget assertions
  tests/test_specstory_coverage.py            # NEW (skips without specstory)
  tests/fixtures/private_key.md               # prose fix
docs/skills/agent-history-hygiene.md          # + .zh-TW.md
~/.local/share/chezmoi/.../create_config.toml # Phase 4, outside repo
```

## Verification

```bash
# Phase 0 — the experiment itself
bash skills/local/agent-history-hygiene/scripts/probe-specstory-redaction.sh --json
bash skills/local/agent-history-hygiene/scripts/probe-specstory-redaction.sh   # table

# Phases 2-3 — full suite (pytest + exit-code contract)
make test-skill

# End-to-end churn check in a throwaway repo: bootstrap, drop a transcript
# containing a real-shape key plus prose mentioning "PRIVATE KEY", commit.
# Expect: hook does NOT modify the file for the bare mention; the key is
# rewritten to [REDACTED:<rule-id>]; a second `git commit` is not required.
cd $(mktemp -d) && git init -q .
bash <repo>/skills/local/agent-history-hygiene/scripts/bootstrap-project.sh
grep -n 'entry:' .pre-commit-config.yaml   # points at .agents/skills/... (or bundled fallback)

# Docs build (bilingual pages must both resolve)
make docs-build
```

## Out of scope

- Backfilling existing `.specstory/history/*.md` to the new placeholder.
- Anything about issue #274 (cloud token in cmdline) beyond a docs note.
- Chasing an upstream `extra_patterns` equivalent — 2.9.0 has none;
  our custom rules stay a local-layer responsibility.
