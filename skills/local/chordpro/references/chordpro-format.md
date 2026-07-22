# ChordPro format reference

Full directive reference for hand-authoring. The cheat-sheet in `SKILL.md`
covers the 90% case; read this when you need something beyond it. Authoritative:
https://www.chordpro.org/chordpro/chordpro-directives/ and
https://www.chordpro.org/chordpro/chordpro-introduction/.

## File + line basics

- Plain UTF-8 text. Recommended extension `.cho`; also recognized `.crd`,
  `.chopro`, `.chord`, `.pro`.
- A line starting with `#` is a **comment** — ignored by the parser (distinct
  from the printed `{comment:}` directive).
- **Blank lines are significant**: they separate verses/blocks.
- A **directive** is a line wrapped in `{ }`. Argument is separated by a colon
  and/or whitespace — all valid:
  - `{title: My Title}` (colon)
  - `{start_of_verse Verse 1}` (whitespace)
  - `{start_of_verse label="Verse 1"}` (explicit attribute — safest when the
    value could be confused for syntax)
- Many directives have a **long and short form** (e.g. `{start_of_chorus}` = `{soc}`).

## Inline chords + annotations

- Chord: `[C]` placed immediately before the syllable it prints above —
  `high[C]er`. Roots/qualities/extensions/bass are parsed (`[C]`, `[Cmaj7]`,
  `[G/B]`, `[F#m7b5]`), which is what makes transpose and re-spelling work.
- Annotation (prints in the chord position but isn't a chord): `[*text]` —
  e.g. `[*softly]`, `[*N.C.]`.
- Text markup (v6+): Pango-like inline markup for size/color/font in lyric and
  directive text; use sparingly and only when the renderer supports it.

## Metadata directives (`{name: value}`)

`title`/`t`, `sorttitle`, `subtitle`/`st`, `artist`, `sortartist`, `composer`,
`lyricist`, `arranger`, `copyright`, `album`, `year`, `key`, `time` (e.g. `4/4`),
`tempo` (e.g. `120`), `duration`, `capo` (integer), and arbitrary
`{meta: name="value"}`. Put these in a block at the top.

## Comment / formatting directives

- `{comment: ...}` / `{c: ...}` — printed comment.
- `{comment_italic: ...}` / `{ci: ...}`, `{comment_box: ...}` / `{cb: ...}`.
- `{highlight: ...}`.
- `{image: src="cover.jpg" scale="50%"}`.

## Environment (paired) directives

Each has a matching `end_of_*`. The **start** may take an optional label; the
**end must NOT repeat any selector/label**.

| Block | Start (long / short) | End | Notes |
|---|---|---|---|
| Chorus | `{start_of_chorus}` / `{soc}` | `{end_of_chorus}` / `{eoc}` | recall later with `{chorus}` or `{chorus: label}` |
| Verse | `{start_of_verse}` / `{sov}` | `{end_of_verse}` / `{eov}` | |
| Bridge | `{start_of_bridge}` / `{sob}` | `{end_of_bridge}` / `{eob}` | |
| Tab | `{start_of_tab}` / `{sot}` | `{end_of_tab}` / `{eot}` | **monospaced; chords NOT parsed** — for ASCII tab |
| Grid | `{start_of_grid}` / `{sog}` | `{end_of_grid}` / `{eog}` | bar/chord grid |
| ABC | `{start_of_abc}` | `{end_of_abc}` | embedded ABC notation (delegated renderer) |
| LilyPond | `{start_of_ly}` | `{end_of_ly}` | embedded LilyPond |
| SVG / textblock | `{start_of_svg}` / `{start_of_textblock}` | matching `end_of_*` | |

**Chorus recall**: `{chorus}` reprints the most-recently-defined chorus and, by
default, renders just a grey "Chorus" label (not the lyrics). With two or more
distinct recurring blocks (e.g. a refrain *and* a chorus), label each —
`{start_of_chorus: Refrain}` … `{chorus: Refrain}` — or expand the repeat inline, or
you'll ship empty "Chorus" tags.

**Instrument / meta selectors** append with a hyphen and may negate with `!`:
`{comment-alto: Very softly}`, `{start_of_verse-soprano}`, `{define-guitar: ...}`.

## Page / layout directives

`{new_song}` / `{ns}`, `{new_page}` / `{np}`, `{column_break}` / `{colb}`,
`{columns: n}` / `{col: n}`, `{transpose: +n}` (per-song, in semitones; `+`/`-`,
optional `s`/`f` spelling).

## Custom namespace

Any directive named `x_...` (e.g. `{x_chordpro_skill_source: youtube}`) **must be
ignored by conformant programs** — a safe place to stash tool-specific metadata
(e.g. mark an auto-generated draft) without breaking rendering.

## Chord diagrams — `{define}`

Define a fingering for any chord. This is also the fix when `chordpro --strict`
warns **"Unknown chord"** for a valid chord (e.g. `Em/C#`, `F#m7b5`): the chord
parses and renders fine — the warning only means there's no *built-in* diagram, so
add a `{define}` and it disappears.

Fretted instruments:

```
{define: Name base-fret N frets f f f f f f [fingers p p p p p p]}
```

- `base-fret` — fret offset of the topmost shown fret (≥ 1).
- `frets` — one value **per string**, low→high (6 by default). `0` = open;
  `-1` / `N` / `x` = muted.
- `fingers` (optional) — `1`–`9` or `A`–`Z`.
- Example (guitar D): `{define: D base-fret 1 frets x x 0 2 3 2}`

Other forms:
- Keyboard: `{define: Name keys note ... note}` (0 = root, 4/3 = third, 7 = fifth,
  11 = maj7).
- Instrument-specific: `{define-guitar: ...}`, `{define-ukulele: ...}`.
- Copy/derive: `{define: A copy B ...}` or `copyall`; suppress one diagram with
  `diagram off`.

## Worked examples

### Chorus recall + tab + capo

```
{title: Example Song}
{key: G}
{capo: 2}

{start_of_verse: Verse 1}
[G]This is a [C]verse with [D]chords
{end_of_verse}

{start_of_chorus}
[Em]Here is the [C]chorus [G]part [D]
{end_of_chorus}

{start_of_verse: Verse 2}
[G]Second verse, [C]same idea [D]here
{end_of_verse}

{chorus}

{start_of_tab: Outro riff}
e|-----0-----|
B|---0---0---|
G|-0-------0-|
{end_of_tab}
```

### Annotation + no-chord + explicit define

```
{define: F#m7b5 base-fret 1 frets 2 x 2 2 1 x}

[*Intro, softly]
[F#m7b5]Falling [*N.C.]silent now
```

## Authoring tips

- Order: metadata block → `{comment}`/environments → verses/choruses; use long
  forms (`{soc}`/`{sov}`/`{sot}`) for readable source, `{chorus}` to avoid
  repeating chorus text.
- Prefer explicit `{key:}` and `{tempo:}` — downstream transpose and rendering
  both use them.
- After writing, **validate** (`scripts/validate-cho.sh`) and consider
  normalizing (`chordpro --generate=ChordPro`).
