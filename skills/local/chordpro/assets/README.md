# chordpro skill — bundled assets

Ready-to-open examples and a template. Use them as copy-paste starting points,
few-shot references when authoring, and fixtures for the scripts.

**All songs here are public domain.** That is deliberate: the skill ships these
in an open repo, so we avoid copyrighted lyrics/arrangements entirely (the same
personal-use / respect-copyright ethos the skill preaches for fetched lyrics and
downloaded audio). Every `.cho` below validates clean with `chordpro --strict`
(0 warnings), verified against ChordPro core 6.101.

| File | Type | Shows | Song / PD basis |
|---|---|---|---|
| `example-amazing-grace.cho` | `.cho` | Simplest real song: metadata block + inline `[C]` chords | Amazing Grace — lyrics J. Newton 1779, tune "New Britain" traditional |
| `example-when-the-saints.cho` | `.cho` | `{start_of_chorus}`/`{start_of_verse}` structure + `{chorus}` recall | When the Saints Go Marching In — traditional gospel |
| `example-greensleeves.cho` | `.cho` | Feature showcase: `{define}` diagrams, `{start_of_tab}` block, chorus recall, transpose note | Greensleeves — English traditional, 16th c. |
| `template-song.cho` | `.cho` | Fill-in-the-blanks scaffold that already renders | original template (no song content) |
| `example-synced-lyrics.lrc` | `.lrc` | Time-synced lyric format (`[mm:ss.xx]`) that `fetch-lyrics.py` returns | Amazing Grace (fabricated but well-formed timestamps) |
| `example-a2crd-input.txt` | `.txt` | Chords-over-lyrics plain text = the **input** to `a2crd` | Amazing Grace |

## Try them

```bash
# validate + render
chordpro -o /tmp/grace.pdf   example-amazing-grace.cho
chordpro -x 3 -o /tmp/g3.pdf example-greensleeves.cho     # transpose up 3 semitones

# convert the chords-over-lyrics sample into ChordPro
chordpro --a2crd example-a2crd-input.txt -o /tmp/converted.cho

# feed the .lrc to the (best-effort) audio pipeline's aligner
uv run ../scripts/audio-to-chords.py --lrc example-synced-lyrics.lrc --dry-run some.wav
```

## How they map to the skill's router

- Editing/rendering an existing sheet → start from any `.cho`.
- "Convert my chords-over-lyrics" → `example-a2crd-input.txt` is the shape to expect.
- "Lyrics only, help me add chords" → open `template-song.cho`, drop the lyrics in,
  fill chords interactively (this is the human-in-the-loop path).
- Audio/link draft → `.lrc` + `audio-to-chords.py` (see `references/audio-to-chords.md`).

## Note on `a2crd` output

`chordpro --a2crd` uses column-position heuristics to place chords, so the
converted `.cho` usually needs a light manual nudge (a chord may land a syllable
early/late). Always validate + eyeball before rendering.
