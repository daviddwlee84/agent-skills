# Fix demo-evidence skill — 22 confirmed defects, in priority order

## Context

The `demo-evidence` skill (`skills/local/demo-evidence/`) was validated against a
real bundle produced in the Ecojoy project. End-to-end it **works** — the bundle
is coherent and demonstrates the feature — but a 33-agent adversarial audit
confirmed **22 defects** (2 plausible, 4 refuted/excluded) in the four scripts +
the Playwright runner. Several are correctness bugs that silently produce wrong
data (mangled session ids, invalid JSON, dropped artifacts); others are
robustness/quality gaps. The user also observed a real symptom: `tutors-list.webm`
is only **1.6s** (vs `booking-flow.webm` 10.8s) — a pure-navigation capture with no
`--steps` records only the brief load→close window.

Goal: fix all confirmed defects in priority order (bugs → robustness → quality →
docs), keeping every script **bash 3.2 compatible** (stock macOS) and portable to
Linux (the `npx skills add` install target). No behavior the audit *refuted* is
touched (e.g. web `--steps` word-splitting — that one is fine).

Files in scope (all under `skills/local/demo-evidence/`):
`scripts/detect-session.sh`, `scripts/new-bundle.sh`, `scripts/capture.sh`,
`scripts/finalize.sh`, `assets/capture-web.mjs`, `SKILL.md`.

---

## Priority 1 — Correctness bugs (produce wrong data)

**B1. `detect-session.sh:114` — SpecStory timestamp regex assumes seconds.**
Regex hard-codes `HH-MM-SS`; real transcripts here are minute-precision
(`2025-07-18_01-25Z-…`), so it never matches and the whole chat title leaks into
`session_id` → bloated session dir. Fix: make seconds optional.
```
sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}(-[0-9]{2})?Z).*/\1/'
```
Verified: yields `2025-07-18_01-25Z` on minute input and `…_15-44-28Z` on second input.

**B2. `detect-session.sh:62` — `cwd_slug` only replaces `/`.**
Claude's real project slug replaces *every* non-alphanumeric char (`.cache`→`--cache`).
Any repo path with `.`/`_`/space misses the jsonl and loses the UUID session.
Fix: `printf '%s' "$PWD" | sed 's/[^a-zA-Z0-9]/-/g'`.

**B3. `detect-session.sh:64-72` — `newest_file` runs `ls` on empty input (GNU xargs).**
On Linux, empty `find` output makes `xargs ls -t` list `$PWD`, fabricating a bogus
jsonl → wrong `agent=claude`/UUID. Fix with an explicit non-empty guard (portable to
BSD + GNU, no reliance on `-r`):
```
list=$(find "$dir" -maxdepth 1 -type f -name "$glob" -print0 2>/dev/null)
[ -n "$list" ] || { printf ''; return 0; }
printf '%s' "$list" | xargs -0 ls -t 2>/dev/null | head -n1
```

**B4. `new-bundle.sh:113 & 166` — stdout JSON hand-built with `printf`, unescaped.**
Exotic branch names/titles (quote in ref, etc.) emit invalid JSON. Fix: build the
result object with `jq -n --arg …` (same pattern already used for `manifest.json`
at lines 133-148). Applies to both the dry-run (113) and final (166) emitters.

**B5. `finalize.sh:205` — final summary JSON shell-interpolates `$BUNDLE` into the jq program.**
Special chars in the path break or inject. Fix: pass via `--arg`:
```
jq -nc --arg b "$BUNDLE" --slurpfile m "$MANIFEST" \
  '{bundle:$b, verdict:$m[0].verdict, artifacts:($m[0].artifacts|length), manifest_md:($b+"/MANIFEST.md")}'
```

## Priority 2 — Robustness

**R1. `finalize.sh:192-195` — `--step` append is non-idempotent.** Re-running
finalize duplicates steps. Fix: only append steps not already present
(`jq 'if (.steps|index($s)) then . else .steps+=[$s] end'`), and document that
finalize is safe to re-run.

**R2. `finalize.sh:95-96` — deleted/missing artifact silently rendered 0 B + broken link.**
Fix: when `[ -f "$BUNDLE/$name" ]` is false, `warn` that the artifact is missing (keep
0 so the table still renders, but the reviewer is told).

**R3. `finalize.sh:107-125` — gitleaks non-zero exit conflated with "secret found".**
gitleaks returns non-zero for *operational* errors too. Fix: capture the exit code and
only treat the leak code (`1`) as a finding; anything else → `warn "gitleaks error"`
without inflating the hit count.

**R4. `capture.sh:77-113` — value-flag as final arg trips `set -e` via `shift 2`.**
`--url` (etc.) with no following value runs `shift 2` with one arg left → non-zero →
bare exit 1, bypassing `die`. Fix: guard each value-flag (`[ $# -ge 2 ] || die "flag $1 needs a value" 1`) or use `shift; shift || true` — mirror across `capture.sh`,
`new-bundle.sh`, `finalize.sh`, `detect-session.sh` for consistency.

**R5. `capture.sh:166-177` + `capture-web.mjs:74-79` — web artifacts discarded on step failure.**
`capture-web.mjs` still writes trace/video and prints the result JSON on failure (exit 5),
but `capture.sh` does `out_json="$(node …)" || die … 5`, so the JSON is thrown away and
nothing is recorded. Fix in `capture.sh`: capture rc separately; on rc==5 still parse
`out_json` and record whatever files exist, appending `note` "(partial: steps failed)".
Only die on rc that isn't 0 or 5.

**R6. `new-bundle.sh:120-130` — absolute `--root` yields malformed `//abs/` gitignore.**
`${ROOT#./}` only strips a leading `./`. Fix: if `$ROOT` is absolute, skip the
`.gitignore` mutation entirely (an absolute path outside the repo can't be a
root-anchored ignore anyway) and rely on the existing `git check-ignore` warning;
for relative roots keep current behavior.

**R7. `new-bundle.sh:163` — `.current` written via truncating redirect (non-atomic).**
Fix: write to `"$ROOT/.current.tmp"` then `mv` into place.

## Priority 3 — Quality / evidence value

**Q1+Q2+Q3. `capture.sh:207-235` (http mode) — restructure the artifact record.**
- Record the `.json` sidecar in the manifest too (currently only `.txt` is recorded).
- Add a structured `status` field to the http artifact instead of smuggling it into
  free-text `note` (fixes the leading-space `" status=307"` when `--note` is empty).
- Add an optional `status`/`meta` field to `add_artifact` so `bytes` vs sidecar `bytes`
  no longer looks contradictory (txt = full dump, json = body only — label them).

**Video. `capture-web.mjs:59-71` — pure-navigation video is a ~1s noise clip.**
Add a short post-screenshot settle (`await page.waitForTimeout(settleMs)` before
`context.close()`, default ~1500ms, and skip/shorten only when no `--steps`), OR make
video opt-out via a `--no-video` flag surfaced through `capture.sh web`. Recommended:
add `--settle MS` (default 1200) so even a no-steps capture yields a usable clip, and
document that steps-driven captures already record their full interaction.

**Q4. `finalize.sh:64-68` — verdict validation case-sensitive.** Accept
`pass|needs_work|PASS|…` by upper-casing before the `case`, and normalize stored value.

**Q5. `finalize.sh:166-169` — Markdown table cells not escaped.** Escape `|` in
`name/kind/tool` (`${x//|/\\|}`) before printing the row so an artifact name with a pipe
can't break the table.

## Priority 4 — Docs (SKILL.md) + pitfalls

**D1. `SKILL.md:47-53` — path example uses a short UUID that a SpecStory-keyed run never
produces.** Update the example to show the realistic minute-stamp form and add a Gotcha:
the session segment length depends on the detected source (Claude UUID → short;
SpecStory → the stamp, now correctly stripped of the title after B1).

**D2. `SKILL.md` Workflow/Gotchas — DB-level claims need captured evidence.** The audit
flagged that the sample bundle *asserts* DB facts (order 480000¢, booking_request rows)
with no artifact backing them, and a screenshot showing logged-out chrome. Add guidance:
for claims not visible in the UI, capture proof (e.g. `capture.sh term --cmd "psql … -c
'select …'"`), and screenshot the logged-in state. This is process guidance, not code.

**Pitfalls entry.** Add `pitfalls/specstory-timestamp-regex-assumes-seconds.md`
(symptom-first: "evidence bundle dir name contains the full chat title") documenting
B1 + B2 root causes and the invariant (SpecStory stamps are minute-precision; Claude
slugs replace all non-alnum). Fits the repo's `pitfalls/` convention.

---

## Verification

Run from repo root; each script is independently testable.

1. **Unit-ish regex/slug checks** (no side effects):
   - `detect-session.sh` B1: feed both `…_01-25Z-title` and `…_15-44-28Z-title` basenames
     through the new sed, assert titles stripped, stamps kept.
   - B2: assert `cwd_slug` on `/x/.cache/y` matches the real `~/.claude/projects` form.
2. **End-to-end dry + real run in a scratch git repo** (`mktemp -d`, `git init`):
   - `new-bundle.sh --title "smoke" --dry-run` then real → assert valid JSON on stdout
     (`| jq .`), `.evidence/` gitignored, `.current` points at the bundle.
   - `capture.sh http --url http://localhost/nope` (or a `python -m http.server`) →
     assert both `http/NAME.txt` **and** `http/NAME.json` appear in `manifest.json`,
     `status` is a structured field, no leading-space note.
   - `capture.sh term --cmd "echo hi"` → artifact recorded; test a value-flag with no
     value (`capture.sh http --url`) exits 1 with the friendly `die` message, not bare.
   - `finalize.sh --verdict pass --step "a" --step "a"` twice → assert steps not
     duplicated, verdict normalized to `PASS`, `MANIFEST.md` renders, summary JSON valid.
   - If Node+Playwright available: `capture.sh web --url … --settle 1500` with no steps →
     assert `.webm` duration > ~1.5s; a failing `--steps` still records partial artifacts.
3. **Re-render the real Ecojoy bundle** with the patched `finalize.sh --bundle <dir>`
   (read-only inputs) to confirm the manifest/MANIFEST.md still render cleanly.
4. Repo hygiene: `make marketplace` (path unchanged, should stay green); add a `TODO.md`
   Done entry via `./scripts/promote-todo.sh` is **not** needed (no open TODO item), but
   record the pitfalls file.

## Out of scope / deferred

- The refuted findings (web `--steps` space word-splitting) — no change.
- Posting `.evidence/` media into a PR (already a tracked `P?` / documented gotcha).
