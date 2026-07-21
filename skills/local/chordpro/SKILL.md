---
name: chordpro
description: Author, convert, validate, render, and transpose ChordPro chord sheets, and build one for a song from an existing online chart, lyrics, or audio. Use when the user mentions ChordPro or .cho/.crd/.pro files, `[C]lyric` inline chords or `{title:}`/`{start_of_chorus}` directives, the `chordpro`/`a2crd` CLI, converting chords-over-lyrics (Ultimate Guitar/OnSong) text, making a guitar chord sheet for a song by name, or extracting chords from a YouTube/Bilibili/SoundCloud link or mp3/wav. References chordpro.org.
---

# chordpro

Produce and work with [ChordPro](https://www.chordpro.org/) chord sheets — the
plain-text format where chords live inline in the lyrics as `[C]like [G]this`.
This skill is a **router that degrades gracefully**: it picks the most reliable
workflow for whatever the user actually has (a `.cho` file, a chords-over-lyrics
paste, bare lyrics, an audio file, or just a song title) and every path ends by
**validating** the output. It is honest about the one hard part — extracting
chords from raw audio is an ~80%-accurate *draft*, never an oracle — and falls
back to interactive, fill-in-the-gaps assistance instead of pretending otherwise.

## When to use

- User names **ChordPro** / `.cho` / `.crd` / `.chopro` / `.pro`, inline
  `[C]lyric` chords, or `{title:}` / `{start_of_chorus}` / `{soc}` directives.
- Convert an existing sheet: **chords-over-lyrics** text (Ultimate Guitar, OnSong,
  a lyric with chord letters on the line above) → ChordPro.
- Render / transpose / validate a `.cho` with the **`chordpro`** or **`a2crd`** CLI.
- "Make a chord sheet for <song>" starting from **lyrics only**, or from a
  **YouTube / Bilibili / SoundCloud link** or an **mp3 / wav** file.
- Ask about **lyrics sources** (Mojim/魔鏡, KKBOX, Musixmatch, LRCLIB, Genius,
  NetEase, QQ Music) — which give time-synced `.lrc` vs plain text.

## When NOT to use

- **Engraving staff notation** (notes on a staff, MusicXML / MIDI / LilyPond /
  MuseScore output) — ChordPro is lyrics+chords, not a score. Hand off to a
  notation tool. (ChordPro *can* embed ABC/LilyPond fragments — see the format
  reference — but it is not an engraver.)
- **OMR from a scanned score image** (photo/PDF of printed sheet music → notes)
  is out of scope; there is no reliable open path. Offer manual transcription
  into ChordPro instead, and say so plainly.

## Authoritative sources

- Format + directives + CLI: **https://www.chordpro.org/** (link, don't
  paraphrase from memory — the directive set evolves).
- Source / releases: **https://github.com/ChordPro/chordpro**.

## The router — pick the workflow by what the user has

| User has… | Do this | Reliability |
|---|---|---|
| A `.cho`/`.crd`/`.pro` file | Render / transpose / **validate** via `chordpro` CLI | High |
| **Chords-over-lyrics** text (UG/OnSong) | `a2crd` → light manual cleanup → validate | High |
| A **known song** (title / lyrics / a link) and no chords yet | **Search existing chord charts online** → adapt to ChordPro (often via `a2crd`) → validate. See `references/chord-tab-sources.md` | Med–High (**best first move**) |
| **Lyrics only**, no chart found | Fetch/confirm lyrics → **interactively** fill chords (propose from key, ask the user to confirm/correct) | Medium (human-in-loop) |
| An **audio file or link**, want a machine draft | `scripts/audio-to-chords.py` → *draft* with `AUTO-GENERATED` header → human correction | ~80% (last resort) |

Prefer the highest row that fits. Two rules that matter: don't jump to the audio
pipeline when the user already pasted chords (`a2crd` is faster and correct); and
for a **named/popular song, search for an existing human-made chart first** — it's
usually more accurate than audio ACR and sidesteps the download-ToS problem
entirely.

## ChordPro cheat-sheet + output template

- **Extensions**: `.cho` (recommended), also `.crd` `.chopro` `.chord` `.pro`.
  Plain UTF-8. `#` starts a comment line; blank lines separate blocks.
- **Inline chords**: `[C]` immediately before the syllable it sits over —
  `Swing [G]low, sweet [C]chari[G]ot`. Annotations (non-chords): `[*softly]`.
- **Metadata**: `{title:}`/`{t:}`, `{subtitle:}`/`{st:}`, `{artist:}`,
  `{composer:}`, `{album:}`, `{year:}`, `{key:}`, `{tempo:}`, `{time:}`, `{capo:}`.
- **Environments** (long / short): chorus `{start_of_chorus}`/`{soc}` …
  `{end_of_chorus}`/`{eoc}`; verse `{sov}`…`{eov}`; bridge `{sob}`…`{eob}`;
  tab (monospaced, chords NOT parsed) `{sot}`…`{eot}`. Recall a chorus with
  `{chorus}`. Comments: `{comment:}`/`{c:}`.

Emit this shape — metadata block → environments/comments → verses/choruses:

```
{title: Swing Low Sweet Chariot}
{artist: Traditional}
{key: G}
{tempo: 90}
{time: 4/4}

{comment: Intro}
[G] [C] [G] [D]

{start_of_chorus: Chorus}
Swing [G]low, sweet [C]chari[G]ot,
Comin' for to carry me [D]home.
{end_of_chorus}

{start_of_verse: Verse 1}
I [G]looked over Jordan, and [C]what did I [G]see,
Comin' for to carry me [D]home.
{end_of_verse}

{chorus}
```

Full directive set (chord `{define}` diagrams, `{transpose}`, markup, ABC/LilyPond
blocks, `x_` custom namespace) → read `references/chordpro-format.md`.

## The `chordpro` / `a2crd` CLI (essentials)

The official tool is a Perl program (CPAN dist **`App::Music::ChordPro`**). Current
6.x releases install the **`chordpro`** command; the chords-over-lyrics importer
is `chordpro --a2crd` (a standalone `a2crd` binary shipped in older releases and
may be absent — prefer `chordpro --a2crd`).

```bash
# Install (macOS — there is NO official Homebrew formula; use CPAN)
brew install perl cpanminus && cpanm App::Music::ChordPro
# If `chordpro` then errors "Can't locate ChordPro.pm", activate local::lib once:
eval "$(perl -I"$HOME/perl5/lib/perl5" -Mlocal::lib)"   # add to ~/.zshrc to persist

# Render
chordpro -o song.pdf song.cho          # PDF (format inferred from extension)
chordpro --generate=HTML -o song.html song.cho

# Transpose (N semitones; suffix s/f forces sharp/flat spelling)
chordpro -x 2  -o up.pdf   song.cho
chordpro -x -3f -o down.pdf song.cho

# Convert chords-over-lyrics text -> ChordPro (the official importer)
chordpro --a2crd input.txt -o song.cho
```

Install-per-platform, generators, config JSON, songbook `--toc`, and `a2crd`
heuristic tuning → read `references/cli-and-rendering.md`.

## Verify loop — never hand back an unvalidated `.cho`

Every generated or edited file goes through the parser before you present it:

```bash
scripts/validate-cho.sh song.cho          # wraps the command below; PASS/FAIL + warnings
# equivalently:
chordpro --strict --generate=Text -o - song.cho   # exit 0 + no stderr warnings = valid
```

To auto-normalize to canonical form (fix spacing, round-trip directives):
`chordpro --generate=ChordPro -o song.cho song.cho`. If `chordpro` isn't
installed, the script prints the install one-liner — say so and offer to proceed
without rendering (the format is still human-checkable).

## Finding existing chord charts (the usual first move)

For a named/popular song, a human-made chart almost always already exists online
and beats audio extraction on accuracy. Search chart sites, pull the
**chords-over-lyrics** block, run it through `chordpro --a2crd`, then validate:

```bash
# 1. search (中文: 吉他谱/和弦/弹唱谱; EN: chords / ultimate guitar)
# 2. WebFetch the best hit, copy the chords-over-lyrics into chart.txt
chordpro --a2crd chart.txt -o song.cho   # 3. convert
scripts/validate-cho.sh song.cho          # 4. validate
```

Caption the result with a `{comment:}` naming the source and "published
arrangement — verify against the recording (capo/key may differ)". This is *not*
machine ACR, so don't use the `AUTO-GENERATED` header — but a web chart is still
one person's arrangement, not ground truth. Site catalog (91譜/Chord4/Ultimate
Guitar/…), format taxonomy, and legality → read `references/chord-tab-sources.md`.

## Generating from audio / links — the fallback when no chart exists

This is the shakiest path — reach for it only when no existing chart is available.

**Set expectations first**: open automatic chord recognition tops out around **78–80% on simple major/minor pop**
and drops sharply on 7ths, extended/jazz chords, key changes, and quiet or dense
mixes; inversions/slash chords are unreliable; and it cannot know the capo a
guitarist used. Treat the result as a **draft to correct**, not a transcription.

```bash
# Best-effort turnkey: link or local file -> draft ChordPro
uv run scripts/audio-to-chords.py --dry-run "https://youtu.be/..."   # show the plan first
uv run scripts/audio-to-chords.py -o draft.cho "https://youtu.be/..."
```

The script downloads audio with `yt-dlp` (YouTube/Bilibili/SoundCloud) and runs
`chord-extractor`/Chordino. Its output **must** carry the
`{comment: AUTO-GENERATED — verify chords/key/timing}` header. On macOS the
Chordino Vamp plugin often isn't installed; the script detects that and prints
exact install guidance + manual alternatives instead of crashing — relay that to
the user rather than silently failing. Tool comparison, beat/key detection, and
commercial escape hatches (Moises/Songsterr have APIs; Chordify/Chord AI/Ultimate
Guitar don't) → read `references/audio-to-chords.md`.

**Legal**: only process content the user owns or has the right to use, for
personal use, locally; downloading copyrighted audio can violate a platform's
ToS. Surface this — don't bury it.

## Lyrics sources

Default to **LRCLIB** — free, no API key, returns time-synced `.lrc`:

```bash
uv run scripts/fetch-lyrics.py --artist "Adele" --track "Hello" --duration 295
uv run scripts/fetch-lyrics.py --plain --artist "..." --track "..."   # plain text
```

| Source | Access | Synced `.lrc`? |
|---|---|---|
| **LRCLIB** | free, no key | **yes** |
| Musixmatch | API key; full/synced is paid | yes (paid) |
| NetEase / QQ Music | unofficial community APIs | yes (Chinese catalog) |
| Genius (`lyricsgenius`) | API token; lyrics scraped from page | no (plain) |
| Mojim / 魔鏡 | scrape-only | no (plain) |
| KKBOX | partner-gated | n/a |

Full comparison, legality, and the LRCLIB API → read `references/lyrics-sources.md`.

## Available scripts

- **`scripts/validate-cho.sh <file.cho>`** — verify a file parses cleanly
  (`chordpro --strict`); PASS/FAIL to stdout, warnings to stderr. Guides install
  if `chordpro` is missing. Flags: `--help`.
- **`scripts/fetch-lyrics.py`** — fetch lyrics from LRCLIB (synced `.lrc` default,
  `--plain` for text). Self-contained via `uv run`. Flags: `--artist`, `--track`,
  `--duration`, `--album`, `--plain`, `--help`, `--dry-run`.
- **`scripts/audio-to-chords.py`** — best-effort link/audio → draft ChordPro
  (`yt-dlp` + `chord-extractor`). Degrades gracefully when the ACR backend is
  unavailable. Flags: `-o/--output`, `--lrc`, `--help`, `--dry-run`.

## Bundled assets

Ready-to-open examples + a template under `assets/` (all songs are **public
domain**; every `.cho` validates clean with `chordpro --strict`). Use them as
copy-paste starting points and few-shot references:

- `assets/example-amazing-grace.cho` — simplest real song: metadata + inline chords.
- `assets/example-when-the-saints.cho` — chorus/verse structure + `{chorus}` recall.
- `assets/example-greensleeves.cho` — feature showcase: `{define}` diagrams, a
  `{sot}` tab block, chorus recall, transpose note.
- `assets/template-song.cho` — fill-in-the-blanks scaffold (renders as-is); the
  starting point for the interactive chord-fill flow.
- `assets/example-synced-lyrics.lrc` — sample time-synced `.lrc` (what
  `fetch-lyrics.py` returns; feed it to `audio-to-chords.py --lrc`).
- `assets/example-a2crd-input.txt` — chords-over-lyrics plain text; convert with
  `chordpro --a2crd assets/example-a2crd-input.txt`.

## Reference files

- `references/chordpro-format.md` — Read **when** hand-authoring or you need a
  directive beyond the cheat-sheet (`{define}` diagrams, `{transpose}`, markup,
  ABC/LilyPond, `x_` custom namespace).
- `references/chord-tab-sources.md` — Read **when** you need chords for a named
  song and have none: where to find existing charts (91譜/Chord4/Ultimate
  Guitar/…), how to adapt them, and the legality.
- `references/cli-and-rendering.md` — Read **when** installing, rendering,
  transposing, converting with `a2crd`, or validating/normalizing.
- `references/audio-to-chords.md` — Read **when** the user wants chords from an
  audio file or a link (ACR tool choice, beat/key, limits, escape hatches).
- `references/lyrics-sources.md` — Read **when** fetching lyrics (source table,
  synced-vs-plain, API-vs-scrape, legality, LRCLIB API).

## Gotchas

- **macOS has no official Homebrew `chordpro`** — install via CPAN
  (`brew install perl cpanminus && cpanm App::Music::ChordPro`). A signed `.dmg`
  GUI exists on GitHub Releases but the CLI is the CPAN route.
- **`Can't locate ChordPro.pm in @INC` after cpanm** — cpanm installed into a
  `local::lib` (`~/perl5`) that isn't on Perl's path. Activate it:
  `eval "$(perl -I"$HOME/perl5/lib/perl5" -Mlocal::lib)"` (persist in `~/.zshrc`).
- **No standalone `a2crd` in ChordPro 6.x** — use `chordpro --a2crd input.txt`.
  Its output needs a human pass (heuristic, column-based chord placement); always
  validate and eyeball before rendering.
- **Angle brackets `< >` are text markup in ChordPro v6.** Don't put `<...>`
  placeholders in lyrics/chords — the parser reads `<b>`/`<i>`-style markup and
  floods warnings. Use plain-text placeholders (see `assets/template-song.cho`).
- **No official online validator.** chordpro.org hosts docs + a desktop GUI, not
  a "try it online" box. Validate locally with the CLI (`validate-cho.sh`).
- **Chord accuracy from audio is ~80% at best** on simple pop, worse otherwise.
  Never present a machine-extracted sheet without the `AUTO-GENERATED` header and
  a "verify chords/key/timing" caveat.
- **Auto-generated chart sites are ACR in disguise.** Chordu / Chordify /
  GuitarTuna charts are machine-derived (~80%, same caveat) — treat them as drafts,
  unlike human-made charts on 91譜 / Chord4 / Ultimate Guitar.
- **Detected key is a suggestion.** ACR outputs absolute pitches; key detection
  confuses relative major/minor and keys a fifth apart, and enharmonic spelling
  (Gb vs F#) is ambiguous. Confirm with the user before committing `{key:}`.
- **Chords in `{sot}`…`{eot}` tab blocks are NOT parsed** — that's for ASCII tab.
  Use inline `[..]` in verses/choruses; reserve tab blocks for fret diagrams.
- **Lyrics/audio ToS.** Prefer LRCLIB (open); most other lyric sources are
  scrape-only or paid, and downloading audio has copyright/ToS limits. Keep it
  personal-use and local; surface the caveat rather than hiding it.
