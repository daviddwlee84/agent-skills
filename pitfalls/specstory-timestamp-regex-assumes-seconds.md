# Evidence bundle dir name contains the full chat title

## Symptom

`demo-evidence`'s `new-bundle.sh` created a session directory whose name is the
entire coding-agent chat title, not a short stable id:

```bash
$ ls .evidence/
claude-2025-07-18_01-25Z-understanding-and-fixing-warning-messages/
#      └── expected: claude-2025-07-18_01-25Z  (stamp only)

$ jq -r '.session.id' .evidence/*/*/manifest.json
2025-07-18_01-25Z-understanding-and-fixing-warning-messages
#                 └── the title leaked into the session id
```

Related failure mode (same script family): on a repo whose path contains `.`,
`_`, or a space, a live Claude session is *not* detected and the bundle keys to a
`specstory`/`unknown` fallback even though a Claude jsonl exists.

## Root cause

Two independent wrong assumptions in `scripts/detect-session.sh`:

1. **SpecStory timestamps were assumed to have seconds.** The title-stripping
   regex hard-coded `HH-MM-SS`:
   `s/^([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}Z).*/\1/`.
   Real SpecStory transcripts are frequently **minute-precision**
   (`2025-07-18_01-25Z-…`, no seconds), so the anchored pattern never matched,
   `sed` passed the input through unchanged, and the whole title became the id.

2. **`cwd_slug` only replaced `/`.** Claude Code's project-dir slug replaces
   **every non-alphanumeric char** (`/Users/me/.cache` → `-Users-me--cache`, note
   the double dash). Replacing only `/` leaves dots/underscores intact, so
   `~/.claude/projects/<slug>` misses and the UUID session is lost.

## Workaround / fix

Make the seconds group optional and slugify all non-alphanumerics:

```bash
# regex: seconds optional
sed -E 's/^([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}(-[0-9]{2})?Z).*/\1/'
# yields 2025-07-18_01-25Z (minute) and 2026-07-07_15-44-28Z (second)

# slug: every non-alnum -> '-'
cwd_slug() { printf '%s' "$PWD" | sed 's/[^a-zA-Z0-9]/-/g'; }
```

## Prevention — the hard invariants

- **SpecStory stamps are `YYYY-MM-DD_HH-MM[-SS]Z` — seconds are OPTIONAL.** Any
  regex over these filenames must treat the seconds field as optional, or it will
  silently no-op and pass the title through.
- **Claude's project slug = `$PWD` with `[^a-zA-Z0-9]` → `-`**, not just `/`.
  Reproduce the exact slug by listing `~/.claude/projects/` and matching, never by
  eyeballing — a dotted repo path is the common miss.
- When a "strip / transform" step relies on a filename format, **verify against a
  real on-disk sample** (here: `.specstory/history/*.md` and
  `~/.claude/projects/*`), not the format you assume upstream uses.

## Where this was hit

Found by an adversarial audit of `demo-evidence` against a real bundle in the
Ecojoy project (`2026-07-07` session). Both bugs were live: the produced bundle
recorded the full-title session id and dir. Fixed in `detect-session.sh`
(seconds-optional regex + all-non-alnum slug); guarded by the skill's end-to-end
verification run.
