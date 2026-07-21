# Plan: Author a `chordpro` agent skill

## Context

The user wants a new local agent skill for the **ChordPro** chord-sheet format
(https://www.chordpro.org/, https://github.com/ChordPro/chordpro). The goal is a
skill that can:

- Convert existing "sheet music" / chords-over-lyrics into ChordPro.
- Know how far automatic chord-extraction can realistically go (open-source ACR
  tools / Hugging Face models), and offer a *best-effort* "paste a
  YouTube/Bilibili/SoundCloud link or mp3/wav → get a draft sheet" path.
- Know the common lyrics sources (Mojim/魔鏡, KKBOX, Musixmatch, LRCLIB, NetEase…).
- When one-shot generation isn't possible, **assist**: fill gaps, ask the user for
  what's missing, guide interactively.
- Know the `chordpro` / `a2crd` CLI.

**Research verdict that shapes the design** (from 3 Explore agents):
- `a2crd` ships with the ChordPro CLI and is the *official* chords-over-lyrics →
  ChordPro converter — the reliable backbone of "convert existing sheets."
- Audio → chords is an **~80%-accurate draft**, not an oracle (MIREX SOTA ~78–80%
  on maj/min, worse on 7ths/jazz/modulations). Best open path: `yt-dlp` →
  `chord-extractor`/Chordino. macOS has a painful Vamp-plugin install; the turnkey
  script must **degrade gracefully**.
- LRCLIB gives free, key-less, time-synced `.lrc`; most other lyric sources are
  scrape-only or paid/partner-gated, with ToS/copyright caveats.

**Confirmed choices (AskUserQuestion):** name = `chordpro`; audio pipeline =
best-effort turnkey script; catalog group = new `music-notation`.

The skill is justified over the no-skill baseline: a stock session does *not*
reliably know the full directive set, `a2crd`, the exact validate command, the
current ACR-tool landscape, or the lyric-source specifics — and the honest
router/interactive-fill framing adds real value.

## Design overview

The skill is a **router that degrades gracefully**. It picks the most reliable
workflow for whatever the user has, and every path ends by validating the `.cho`:

| User has… | Workflow |
|---|---|
| A `.cho`/`.crd`/`.pro` file | Render / transpose / validate via `chordpro` CLI |
| Chords-over-lyrics text (Ultimate Guitar / OnSong) | `a2crd` → clean up → validate |
| Lyrics only | Fetch/confirm lyrics → interactive chord-fill (agent proposes from key + asks user) |
| An audio file or link | Best-effort `audio-to-chords.py` (honest ~80% draft) → human correction |
| Only a song title | Fetch lyrics (LRCLIB) + optionally audio → pipeline or interactive fill |

## Scaffold

Author downstream-only (not useful while working *on this repo*), so **no**
discovery symlinks:

```bash
bash skills/local/skill-author/scripts/new-skill.sh --local --no-symlinks chordpro
```

Canonical dir: `skills/local/chordpro/` (this copy is what ships).

## Files to create

### `skills/local/chordpro/SKILL.md` (~220–260 lines)

Follow the repo's section skeleton (matches `slurm-hpc`/`dvc-ml-workflow`).

- **Frontmatter description** — pushy, ~450 chars (within 120–500 preferred),
  with concrete triggers + upstream docs. Draft:
  > Author, convert, validate, render, and transpose ChordPro chord sheets, and
  > generate them from lyrics or audio. Use when the user mentions ChordPro or
  > `.cho`/`.crd`/`.pro` files, `[C]lyric` inline chords or
  > `{title:}`/`{start_of_chorus}` directives, the `chordpro`/`a2crd` CLI,
  > converting chords-over-lyrics (Ultimate Guitar/OnSong) text, fetching lyrics
  > (LRCLIB/Mojim/Musixmatch), or extracting chords from a
  > YouTube/Bilibili/SoundCloud link or mp3/wav. References chordpro.org.
- **Overview** — one paragraph: opinionated router + honest draft-assistant scope.
- **When to use / When NOT to use** — NOT for engraving staff notation
  (MusicXML/MIDI/LilyPond → hand off); OMR from a scanned score *image* is out of
  scope (note it, offer manual transcription instead).
- **Authoritative sources** — chordpro.org, ChordPro/chordpro repo (link, don't
  paraphrase).
- **The router** — the decision table above.
- **ChordPro cheat-sheet + output template** — extensions, `[C]lyric`, core
  directives, chorus/verse/tab environments, and one compact well-formed `.cho`
  example (from research) as the copy-paste template. Defer the full directive
  set to `references/chordpro-format.md`.
- **The `chordpro`/`a2crd` CLI (essentials)** — macOS install one-liner
  (`brew install perl cpanminus && cpanm App::Music::ChordPro`), render
  (`chordpro -o song.pdf song.cho`), transpose (`-x N[s|f]`), `a2crd input.txt`.
  Defer detail to `references/cli-and-rendering.md`.
- **Verify loop** — always validate generated files:
  `chordpro --strict --generate=Text -o - file.cho` (exit 0 + no stderr = valid);
  auto-normalize with `--generate=ChordPro`. Wrapped by `scripts/validate-cho.sh`.
- **Generating from audio/links (honest limits)** — the ~80% caveat, the
  mandatory `AUTO-GENERATED — verify chords/key/timing` header, `audio-to-chords.py`
  usage, and the **personal-use / ToS / copyright** disclaimer. Defer to
  `references/audio-to-chords.md`.
- **Lyrics sources** — quick table, default LRCLIB. Defer to
  `references/lyrics-sources.md`.
- **Available scripts / Reference files / Gotchas** — per below.

### `skills/local/chordpro/references/` (4 files, loaded lazily)

- `chordpro-format.md` — full directive reference (metadata, comment,
  environments, `{define}` chord-diagram syntax, `{transpose}`, markup, `x_`
  custom namespace) + worked examples (chorus recall, tabs, capo). *Read when
  hand-authoring or needing a directive beyond the cheat-sheet.*
- `cli-and-rendering.md` — install per platform; generators (PDF/Text/ChordPro/HTML);
  transpose/`--decapo`; config JSON; songbook `--toc`; validate/normalize; `a2crd`
  usage + heuristic tuning. *Read when installing, rendering, transposing,
  converting, or validating.*
- `audio-to-chords.md` — the feasibility pipeline in depth: `yt-dlp` commands
  (YouTube/Bilibili/SoundCloud, `--cookies-from-browser` for gated content); ACR
  tool comparison (chord-extractor/Chordino default, madmom CNN higher-accuracy,
  Omnizart heavyweight, HF demos as research-grade only); beat/key helpers
  (madmom/librosa/Essentia); explicit limitations; commercial escape hatches
  (Moises API, Songsterr API, Chordify/Chord AI/UG = no API); legal note. *Read
  when the user wants chords from audio/a link.*
- `lyrics-sources.md` — source table (LRCLIB / Musixmatch / Genius / Mojim / KKBOX
  / NetEase / QQ), synced-vs-plain, API-vs-scrape, legal notes, LRCLIB API details.
  *Read when fetching lyrics.*

### `skills/local/chordpro/scripts/` (3 scripts, all with `--help`)

1. **`validate-cho.sh`** (bash 3.2, `set -euo pipefail`) — agent-facing verify
   loop. Runs `chordpro --strict --generate=Text -o - "$FILE"`, prints `PASS`/`FAIL`
   (data→stdout, warnings→stderr), propagates exit code. If `chordpro` isn't
   installed, prints the install one-liner and exits non-zero with guidance.
2. **`fetch-lyrics.py`** (PEP 723 `# /// script`, `uv run`, dep: `httpx`) — query
   LRCLIB `/api/get` (fallback `/api/search`) by `--artist/--track/--duration`;
   emit synced `.lrc` by default or `--plain`; structured stdout, diagnostics to
   stderr; `--help`, `--dry-run`. LRCLIB only (free, no key, cross-platform);
   documents other sources as manual/reference. No scraping shipped.
3. **`audio-to-chords.py`** (PEP 723, dep: `yt-dlp`; `chord-extractor` guarded) —
   best-effort turnkey draft generator:
   - Input: a URL (via `yt-dlp` → bestaudio → wav, needs `ffmpeg`) **or** a local
     audio file. `--dry-run` prints the plan without downloading.
   - Runs `chord-extractor`/Chordino → chord/timestamp timeline. **If the Vamp
     plugin/import is missing (common on macOS), detect it and print exact install
     guidance + the `sonic-annotator`/`madmom` manual alternatives, then exit
     cleanly** — the degrade-gracefully contract the user chose.
   - Emits a ChordPro *skeleton* with the mandatory `AUTO-GENERATED` header,
     best-guess `{key}`/`{tempo}` (optional librosa), chords placed per
     bar/line; if an `.lrc`/lyrics arg is supplied, attempt line-level chord
     placement. Structured stdout (path/text), prose to stderr.
   - `--help` carries the personal-use / ToS / copyright disclaimer.

**Reuse:** these three wrap the *official* tools the research surfaced
(`chordpro`, `a2crd`, LRCLIB API, `yt-dlp`, `chord-extractor`) rather than
reimplementing anything.

## Register in the marketplace

Edit `skills/.claude-plugin/marketplace.json` — add a new **unprefixed** group
(sorts alphabetically among unprefixed groups; that's fine):

```json
{ "name": "music-notation", "skills": ["./local/chordpro"] }
```

Then `make marketplace` (runs `scripts/validate-marketplace.sh` — checks paths,
dupes, reserved names).

## Optional follow-ups (defer, don't build now)

- `./scripts/add-todo.sh --priority P? --effort M --title "chordpro: higher-accuracy ACR mode + word-level chord alignment" --description "…"` — madmom CNN path + syllable-level placement once the v1 draft flow is proven.
- Docs-catalog cross-listing: no music/creative domain hub exists; skip for v1.

## Verification

1. `bash skills/local/skill-author/scripts/lint-skill.sh skills/local/chordpro`
   → frontmatter valid, description within limits, SKILL.md < 500 lines, every
   `references/*.md` mentioned from SKILL.md, every script has shebang + `+x` +
   `--help`. Fix all errors.
2. `make marketplace` → passes with `./local/chordpro` under `music-notation`.
3. Script smoke tests (all must work even if `chordpro` isn't installed here —
   they should guide, not crash):
   - `bash skills/local/chordpro/scripts/validate-cho.sh --help`
   - Create a tiny sample `.cho`; run `validate-cho.sh sample.cho` (if `chordpro`
     present, expect PASS; else expect the install-guidance path).
   - `uv run skills/local/chordpro/scripts/fetch-lyrics.py --dry-run --artist "…" --track "…"`, then one real LRCLIB query.
   - `uv run skills/local/chordpro/scripts/audio-to-chords.py --dry-run <url>` →
     prints the plan; a real run on a short public clip exercises the
     download → ACR → skeleton path (or the graceful-degrade message on macOS).
4. Spot-check the output template renders: `chordpro -o /tmp/test.pdf sample.cho`
   (only where the CLI is installed).
