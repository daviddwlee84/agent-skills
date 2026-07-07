# Plan: `demo-evidence` local skill

## Context

Reviewing an agent's feature today means reading the diff or manually
booting the app to try it. We want the agent to leave behind **acceptance
evidence** — screenshots, screen/terminal recordings, request logs — so a
human (or a later agent) can validate the work asynchronously, à la
Cursor Cloud Agent's "Demos over diffs".

`/find-skills` surfaced no reusable skill for this (the demo-video skills
are marketing-oriented, <600 installs). The real building blocks are
Playwright/asciinema/ffmpeg + a disciplined "evidence bundle" convention.
This repo already has adjacent skills (`verifiable-surfaces`, global
`verify`/`run`) but none that **captures and files** the evidence.

**Goal:** a `skills/local/demo-evidence/` skill that records capture
artifacts into a `.gitignore`-protected `.evidence/` tree, each bundle
keyed to the coding-agent session + git branch/commit/date, with a
machine- and human-readable manifest, ready for local sign-off.

## Locked decisions (from user)

- **Name:** `demo-evidence`
- **Layout:** session-grouped, and the session dir is **tagged with the
  agent kind** (`claude` / `cursor` / `codex` / …).
- **Capture modes in v1:** all four — Web (Playwright), Terminal
  (asciinema), HTTP/API (curl logs), Screen recording (ffmpeg) — pick per
  app type.
- **PR posting:** **out of scope for v1** (local `.evidence/` only).
  Record a `TODO P?` backlog item for it (gist-raw-URL image embed + video
  links + mandatory secret-scrub-before-publish).

## Directory & naming design

```
.evidence/                                   # gitignored (self-scoped .gitignore)
  .gitignore                                 # "*\n!.gitignore" — commit nothing but self
  claude-3f9a2c1b/                           # <agent>-<session-slug>
    2026-07-07T10-33-39Z-6526681-login/      # <UTC-ts>-<shortSHA>[-<title-slug>]
      manifest.json                          # machine-readable (schema below)
      MANIFEST.md                            # human-facing: verdict, steps, links
      login-desktop.png
      login-flow.webm
      trace.zip
      server.log
  cursor-a17c9f/
    2026-07-07T14-02-10Z-8308efe/
      ...
```

- Timestamp: `date -u +%Y-%m-%dT%H-%M-%SZ` (colon-free, sortable, mirrors
  SpecStory's `YYYY-MM-DD_HH-MM-SSZ` UTC idiom — `scripts/sync-vendor.sh:184`
  uses the ISO form, we swap `:`→`-` for filenames).
- Branch/SHA still recorded **inside** every manifest regardless of the
  session grouping (so a bundle is self-describing).
- `<session-slug>` = Claude session UUID (short prefix) or SpecStory
  timestamp; `nosession` fallback. `<agent>` = detected or `--agent`
  override; `unknown` fallback.

### `manifest.json` schema (v1)

```jsonc
{
  "schema": 1,
  "created_utc": "2026-07-07T10:33:39Z",
  "agent": "claude",
  "session": { "id": "3f9a2c1b…", "source": "claude_jsonl",
               "specstory_path": ".specstory/history/2026-07-07_10-33-39Z-….md" },
  "git": { "branch": "feat/login", "sha": "6526681", "dirty": true },
  "title": "login flow", "feature": "…",
  "verdict": "pending",                      // pending | PASS | NEEDS_WORK
  "steps": ["reproduction step 1", "…"],
  "artifacts": [
    { "name": "login-desktop.png", "kind": "screenshot", "tool": "playwright", "bytes": 12345 },
    { "name": "login-flow.webm",   "kind": "video",      "tool": "playwright" }
  ]
}
```

## Scripts to build (`skills/local/demo-evidence/scripts/`)

All Bash 3.2-compatible, `set -euo pipefail`, `usage()` heredoc with
`--help/-h` + `--dry-run`, **diagnostics→stderr / data(JSON)→stdout**,
numbered exit codes — matching the repo template
(`skills/local/skill-author/assets/script-bash.template`) and the
`verifiable-surfaces` convention. `jq` used for manifest edits (already a
repo-wide dependency).

1. **`detect-session.sh`** — best-effort `{agent, session_id, source,
   specstory_path}` JSON; always exit 0. Self-contained mirror of
   `skills/local/agent-history-hygiene/scripts/find-session.sh` core
   (Claude UUID = newest `*.jsonl` under `~/.claude/projects/<PWD-slug>/`
   where slug = `printf '%s' "$PWD" | sed 's|/|-|g'`; SpecStory = newest
   `./.specstory/history/*.md`). Agent kind via env (e.g. `$CLAUDECODE`)
   + artifact-dir presence (`.cursor/`, `.codex/`, `.specstory/`), with
   `--agent` override. **Self-contained on purpose** — downstream users
   may install `demo-evidence` alone, so no hard cross-skill path dep.

2. **`new-bundle.sh`** — the entrypoint. Guards
   `git rev-parse --show-toplevel` (copy `stage-agent-artifacts.sh:68-72`);
   reads `git rev-parse --short HEAD`, `git rev-parse --abbrev-ref HEAD`,
   dirty via `git status --porcelain` (idioms confirmed in-repo). Calls
   `detect-session.sh`. Creates the bundle dir, writes `manifest.json` +
   `MANIFEST.md` scaffold (from `assets/manifest-template.md`). Ensures
   `.evidence/` is ignored: create `.evidence/.gitignore` (`*` + `!.gitignore`)
   and verify with `git check-ignore -q .evidence`
   (idiom: `stage-agent-artifacts.sh:88-93`); warn if not. Prints
   `{bundle_dir, manifest, agent, session, branch, sha, dirty}` JSON.

3. **`capture.sh <mode>`** — dispatcher over the four modes; `--bundle DIR`
   (defaults to newest bundle by mtime); appends an `artifacts[]` entry to
   `manifest.json` via `jq`. Each mode preflights its tool (`command -v …`
   pattern from `enable-pages.sh:60-61`) and degrades with a clear stderr
   hint:
   - `web`  → runs bundled `assets/capture-web.mjs` via pinned
     `npx --yes playwright@<pin>` → screenshot + `recordVideo` webm +
     `trace.zip`. (Richer alternative documented: `microsoft/playwright-cli`
     skill, 78K installs.)
   - `term` → `asciinema rec <bundle>/term.cast -c "<cmd>"`; fallback
     `script`. `--log "<cmd>"` mode tees stdout+stderr to `<bundle>/<n>.log`
     and records exit code.
   - `http` → curl one request or a sequence file → status + headers +
     body + timing into `<bundle>/http/<n>.txt` (+ `.json` summary).
   - `screen` → ffmpeg (`avfoundation` on darwin / `x11grab` on linux),
     timed or start/stop → `<bundle>/screen.mp4`.

4. **`finalize.sh`** — set `--verdict PASS|NEEDS_WORK`, fill the artifact
   inventory + byte sizes into both manifests, render `MANIFEST.md`
   (relative links + review checklist), print a human summary + JSON.
   `--scrub` (opt-in) runs gitleaks over text artifacts (`*.log`,
   `http/*.txt`) if available and **warns that screenshots/video can't be
   auto-scrubbed** — mirrors the redaction posture of
   `agent-history-hygiene/assets/redact_secrets.py` (masks, doesn't delete).

### Assets (`skills/local/demo-evidence/assets/`)

- `capture-web.mjs` — minimal Playwright runner (open URL, optional steps
  file, save screenshot/video/trace to `--out`).
- `manifest-template.md` — `MANIFEST.md` scaffold with placeholders.

### `SKILL.md`

Frontmatter `name` + `description` only (pushy, ≥3 trigger contexts:
"record a demo", "leave acceptance evidence", "capture screenshots/video
of a feature", "prove the change works for review"). Body per repo template
order: overview → When to use / When NOT to use → Workflow (`new-bundle` →
`capture …` → `finalize`) → Available scripts (flags + exit codes) →
Bundled assets → Gotchas (**keep**: gitignored media has no public URL so
it can't embed in a PR; screenshots can leak secrets — human must review;
Playwright needs node; ffmpeg screen-record needs macOS screen-recording
permission). Keep <500 lines. Cross-reference global `run`/`verify`
(drive the app) vs. this skill (record the evidence).

## Registration & housekeeping

- **marketplace.json** — add `./local/demo-evidence` to the group that
  holds `agent-history-hygiene` / `verifiable-surfaces` /
  `project-knowledge-harness` (agent-harness/workflow); else it falls to
  "Other". Run `make marketplace`.
- **Symlinks** — scaffold with `--no-symlinks` (downstream-oriented; the
  repo's product is prose+bash skills with little runtime surface to demo
  in-repo). Note in handoff that the user can add discovery symlinks later
  if they want it live while working on this repo.
- **Docs** — add `docs/skills/demo-evidence.md`, an index row in
  `docs/skills/index.md`, an `mkdocs.yml` nav entry, and a README
  "What's in here" row (follow the existing `docs/skills/` bilingual/EN
  convention of neighboring pages).
- **Backlog (user-requested)** —
  `./scripts/add-todo.sh --priority P? --effort M --title "demo-evidence: PR
  posting" --description "gh pr comment: post MANIFEST text + gist-raw-URL
  image embed (video as link); mandatory gitleaks/redact pass before any
  external publish since .evidence/ media has no public URL"`.
- **pitfalls (optional)** — `pitfalls/evidence-gitignored-media-cannot-embed-in-pr.md`
  documenting the local-folder ↔ PR-embed tension for future agents.
- **Lint** — `bash skills/local/skill-author/scripts/lint-skill.sh
  skills/local/demo-evidence` before handoff.

## Reused idioms (do not reinvent)

| Need | Source |
|---|---|
| repo-root guard | `agent-history-hygiene/scripts/stage-agent-artifacts.sh:68-72` |
| dirty status (porcelain -z) | same file `:132` |
| gitignore check | same file `:88-93` (`git check-ignore -q`) |
| session/agent detection | `agent-history-hygiene/scripts/find-session.sh` |
| secret-scrub posture | `agent-history-hygiene/assets/redact_secrets.py` |
| gh/tool preflight + `--dry-run` | `mkdocs-site-bootstrap/scripts/enable-pages.sh:60-88` |
| UTC timestamp | `scripts/sync-vendor.sh:184` (ISO → colon-free for filenames) |
| bash script skeleton | `skill-author/assets/script-bash.template` |
| script UX bar (`--help/--dry-run`/exit codes) | `verifiable-surfaces` |

## Verification (end-to-end)

1. `bash skills/local/demo-evidence/scripts/detect-session.sh` → prints
   JSON with a plausible `agent` + `session_id` in this Claude session.
2. `new-bundle.sh --title smoke` → creates
   `.evidence/<agent>-<session>/<ts>-<sha>-smoke/` with both manifests;
   `git check-ignore .evidence` confirms it's ignored; `git status` shows
   no new tracked files.
3. `capture.sh term --log "printf hi"` → `hi.log` in the bundle +
   `artifacts[]` grows in `manifest.json`.
4. `capture.sh http --url https://example.com` → `http/example.txt` with
   status 200; `capture.sh web --url https://example.com` (if node
   available) → screenshot + webm + trace.
5. `finalize.sh --verdict PASS` → `MANIFEST.md` lists every artifact with
   sizes and a `PASS` verdict; `--scrub` on a log seeded with a fake
   `sk-…` key masks it (or warns if gitleaks absent).
6. `make marketplace` passes; `lint-skill.sh` passes; `make kanban` passes
   after the `add-todo.sh` entry.

## Out of scope (v2 / backlog)

- Any PR/GitHub posting (tracked as `TODO P?`).
- Publishing media to durable URLs (gist raw for images, CDN for video).
- Visual-regression baselines / Lighthouse / axe — capture only, no gating.
