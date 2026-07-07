---
name: demo-evidence
description: Capture acceptance evidence — screenshots, terminal/screen recordings, HTTP logs — for a just-built feature into a gitignored .evidence/ bundle keyed to git branch/commit + coding-agent session, for async human validation (Cursor "Demos over diffs" style). Use when the user says "record a demo", "leave evidence", "capture a screenshot/video", "prove it works", wants async sign-off / 驗收, or asks to show a feature works without reading the diff or booting the app by hand. Playwright/asciinema/curl/ffmpeg.
---

# demo evidence

Reviewing an agent's work usually means reading the diff or booting the app
by hand. This skill has the agent **leave behind acceptance evidence** —
screenshots, screen/terminal recordings, request logs — filed into a
`.gitignore`-protected `.evidence/` tree, each bundle keyed to the git
branch/commit and the coding-agent session that produced it. A reviewer (or a
later agent) opens the bundle's `MANIFEST.md`, watches the demo, and signs off
— no re-driving the app.

The lifecycle is three scripts: **`new-bundle.sh`** (open a bundle) →
**`capture.sh`** (add artifacts, once per surface) → **`finalize.sh`** (stamp a
verdict and render the review page). Complements the global `run` / `verify`
skills: use *those* to drive the app; use *this* to record what they showed.

## When to use

- User says "record a demo of this", "leave evidence", "capture a
  screenshot/video of the feature", "prove it works", "demos over diffs".
- User wants **async 驗收 / sign-off** — they'll review later, not watch you now.
- You just finished a feature and want the acceptance artifacts to live
  next to the branch/commit that produced them.
- A reviewer asked "show me it works" without reading the diff.

## When NOT to use

- The change has **no runtime surface** (docs, comments, pure refactor with
  tests) → nothing to demo; point at the tests.
- You just need to *drive* the app to check it yourself → global `run` /
  `verify`. Only reach here when you want a **filed, reviewable artifact**.
- Posting media **into a PR** → not in v1. `.evidence/` is gitignored, so its
  images/videos have no public URL to embed (see Gotchas). Tracked as a `P?`
  backlog item.

## Workflow

### 1. Open a bundle

```bash
bash skills/local/demo-evidence/scripts/new-bundle.sh \
  --title "login flow" --feature "Verify login redirects to /dashboard"
# stdout: {"bundle_dir":".evidence/claude-5f932f43/2026-…-6526681-login-flow", ...}
```

Detects the agent session + git branch/short-SHA/dirty, creates
`.evidence/<agent>-<session>/<UTC-ts>-<shortSHA>[-<title>]/`, writes
`manifest.json` + a `MANIFEST.md` scaffold, ensures `.evidence/` is gitignored,
and records the path in `.evidence/.current`. Later steps default to
`.current`, so you rarely pass `--bundle`. The `<session>` segment is a short
Claude jsonl UUID (`claude-5f932f43`) when a live Claude session is detected, or
the SpecStory timestamp stamp (`claude-2025-07-18_01-25Z`) when keyed off a
`.specstory/history/*.md` transcript — the chat title is stripped from the id.

### 2. Capture one artifact per surface

Pick the mode(s) that fit the app. Each appends to the bundle manifest.

```bash
CAP="bash skills/local/demo-evidence/scripts/capture.sh"

# Web UI — full-page screenshot + video + Playwright trace
$CAP web  --url http://localhost:3000/login --name login --steps ./demo-steps.mjs

# CLI / TUI — asciinema recording (falls back to a plain tee'd log)
$CAP term --cmd "mytool --do-the-thing" --name run

# HTTP / API — status + headers + body + timing
$CAP http --url http://localhost:8000/health --name health

# Desktop / non-browser GUI — timed screen recording
$CAP screen --seconds 10 --name walkthrough
```

Capture what actually demonstrates the feature — don't capture blindly. A
before/after screenshot pair or a 10-second flow beats a folder of noise.

**Evidence a reviewer can't re-derive from the UI must be captured, not just
asserted.** If your `--feature`/`--step` text claims a DB row, a computed total,
or a background side effect (e.g. "order priced at 480000¢", "booking_request
row created"), capture proof — e.g. `capture.sh term --cmd "psql … -c 'select …'"`
or an `http` probe of the API that returns it. Likewise, screenshot the
**logged-in** state when the claim is "user logs in": a shot showing logged-out
chrome undercuts the story. The manifest's steps are the script; the artifacts
are the proof.

### 3. Finalize for review

```bash
bash skills/local/demo-evidence/scripts/finalize.sh \
  --verdict PASS \
  --step "open /login" --step "submit valid creds" --step "expect /dashboard" \
  --scrub
```

Stamps the verdict, appends reproduction steps, refreshes artifact sizes, runs
an optional secret scan, and renders the human-facing `MANIFEST.md` (verdict
badge, context, repro steps, artifact table, review checklist). Point the
reviewer at `<bundle>/MANIFEST.md`.

## Available scripts

- **`scripts/new-bundle.sh`** — Create a bundle keyed to session + git; emit its path as JSON. Guarantees `.evidence/` is gitignored.
  - Flags: `--title`, `--feature`, `--agent`, `--root`, `--dry-run`, `--help`.
  - Exit: `0` ok, `1` bad args, `2` not a git repo, `3` jq missing.
- **`scripts/capture.sh <web|term|http|screen>`** — Capture one artifact into a bundle (default `.current`) and record it in `manifest.json`.
  - Common: `--bundle`, `--root`, `--name`, `--note`, `--dry-run`.
  - `web`: `--url`, `--steps`, `--timeout`. `term`: `--cmd`, `--log`. `http`: `--url`, `--method`, `--data`, `--header` (repeatable). `screen`: `--seconds`, `--device`, `--display`.
  - Exit: `0` ok, `1` bad args, `2` no bundle, `3` jq missing, `4` capture tool missing, `5` capture failed.
- **`scripts/finalize.sh`** — Set verdict, append steps, refresh sizes, optional secret scan, render `MANIFEST.md`.
  - Flags: `--bundle`, `--root`, `--verdict PASS|NEEDS_WORK|pending`, `--step` (repeatable), `--scrub`, `--dry-run`, `--help`.
  - Exit: `0` ok, `1` bad args, `2` no bundle, `3` jq missing.
- **`scripts/detect-session.sh`** — Best-effort `{agent, session_id, source, specstory_path}` JSON. Standalone or called by `new-bundle.sh`.
  - Flags: `--agent`, `--json`/`--tsv`, `--quiet`, `--help`. Exit: `0` always, `1` bad args.

## Bundled assets

- `assets/capture-web.mjs` — Minimal Playwright runner (screenshot + video +
  trace) invoked by `capture.sh web`. Loads `playwright` from the project's
  `node_modules` via `createRequire(cwd)`.

## Gotchas

- **`.evidence/` media has NO public URL — it cannot embed in a GitHub PR.**
  The whole point is a gitignored local surface, so images/videos aren't
  web-reachable. Posting to a PR (gist-raw-URL image embed, video links) is a
  deliberate `P?` backlog item, out of scope for v1. For now, share the bundle
  locally or push it out-of-band.
- **Screenshots and logs can leak secrets, and screenshots can't be
  auto-scrubbed.** `finalize.sh --scrub` only *reports* on text artifacts
  (`*.log`, `*.txt`) via gitleaks — a human must eyeball images/video before
  sharing them anywhere. Because `.evidence/` is gitignored, nothing reaches
  git history, but external sharing is on you.
- **`capture.sh web` needs Node + Playwright installed in the project.** If
  `playwright` doesn't resolve from the CWD it exits `4` with an install hint
  (`npm i -D playwright && npx playwright install chromium`) — or use the
  `microsoft/playwright-cli` skill as the browser engine instead.
- **A `web` capture with no `--steps` records a short video.** Playwright records
  for the context lifetime, so a bare `goto → screenshot → close` yields a ~1–2s
  clip. `capture.sh web` holds the final state for `--settle MS` (default 1200)
  before closing so the clip is usable; raise `--settle` for a longer hold, or
  drive real interaction via `--steps` (which records the whole flow). If a
  Playwright step throws, the capture still records the partial screenshot/video/
  trace (noted `(partial: capture failed)`) instead of discarding them.
- **`capture.sh screen` on macOS needs Screen Recording permission** and the
  right avfoundation device index (default `1`, varies per machine). List
  devices with `ffmpeg -f avfoundation -list_devices true -i ""` and pass
  `--device`. On Linux it uses `x11grab` on `$DISPLAY`.
- **Agent detection is best-effort.** Env markers (`$CLAUDECODE`, `$CURSOR_*`,
  `$CODEX_*`) then artifact presence; falls back to `unknown`. Pass
  `--agent cursor|codex|…` to `new-bundle.sh` when the session isn't yours.
- **`term` falls back to a plain log without asciinema.** The log still
  captures stdout+stderr and the command's exit code, but not timing/replay.
  Install `asciinema` for a replayable `.cast`.
- **Bundles default to `.evidence/.current`.** Running a second `new-bundle.sh`
  repoints `.current`; pass `--bundle DIR` to capture into an older bundle.
