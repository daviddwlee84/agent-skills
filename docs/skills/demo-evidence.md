# demo-evidence

Have an agent **leave behind acceptance evidence** — screenshots,
screen/terminal recordings, HTTP logs — for a feature it just built, filed
into a `.gitignore`-protected `.evidence/` tree, so a human (or a later
agent) can validate the work asynchronously instead of reading the diff or
booting the app by hand. This is the Cursor "Demos over diffs" idea, done
locally and git-safe.

Each **bundle** is keyed to the coding-agent session that produced it and
the git branch/commit at capture time, and self-describes via a
`manifest.json` (machine-readable) + `MANIFEST.md` (human review page).

## Layout

```
.evidence/                                   # gitignored (root .gitignore entry)
  claude-5f932f43/                           # <agent>-<session>
    2026-07-07T11-11-29Z-6526681-login-flow/ # <UTC-ts>-<shortSHA>[-<title>]
      manifest.json
      MANIFEST.md
      login.png / login.webm / login-trace.zip
      run.log
      http/health.txt
```

## Lifecycle (three scripts)

1. **`new-bundle.sh`** — open a bundle: detect agent session + git
   branch/short-SHA/dirty, create the dir, scaffold manifests, guarantee
   `.evidence/` is gitignored, and record `.evidence/.current`.
2. **`capture.sh <web|term|http|screen>`** — add one artifact per surface and
   record it in `manifest.json`:
   - `web` → Playwright full-page screenshot + video + trace
   - `term` → asciinema recording (falls back to a tee'd log)
   - `http` → curl status + headers + body + timing
   - `screen` → ffmpeg screen recording (macOS avfoundation / Linux x11grab)
3. **`finalize.sh`** — stamp a verdict (`PASS`/`NEEDS_WORK`), append
   reproduction steps, refresh artifact sizes, optionally secret-scan text
   artifacts, and render the `MANIFEST.md` review page.

```bash
NB=skills/local/demo-evidence/scripts
BUNDLE=$(bash $NB/new-bundle.sh --title "login flow" --feature "login redirects to /dashboard" | jq -r .bundle_dir)
bash $NB/capture.sh term --cmd "mytool --demo" --name run
bash $NB/capture.sh http --url http://localhost:8000/health --name health
bash $NB/finalize.sh --verdict PASS --step "open /login" --step "submit creds" --scrub
```

## When to use / not use

Use it when the user wants **async 驗收 / sign-off** on an agent's work, says
"record a demo", "leave evidence", "prove it works", or a reviewer asks
"show me it works" without reading the diff. Skip it for changes with no
runtime surface (docs, pure refactors covered by tests) — there's nothing to
demo.

## Known limits (v1)

- **`.evidence/` media cannot embed in a GitHub PR** — a gitignored file has
  no public URL. PR posting (text manifest + gist-raw-URL image embed) is a
  tracked `P?` backlog item, out of scope for v1.
- **Screenshots/video can't be auto-scrubbed** for secrets — `finalize.sh
  --scrub` only reports on text artifacts via gitleaks; a human eyeballs the
  rest before sharing externally.
- **`capture.sh web` needs Node + Playwright** in the project; `screen` needs
  ffmpeg (+ macOS Screen Recording permission).

## Canonical SKILL.md

See [skills/local/demo-evidence/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/demo-evidence/SKILL.md)
for the full triggering description, workflow, script flags/exit codes, and
gotchas.
