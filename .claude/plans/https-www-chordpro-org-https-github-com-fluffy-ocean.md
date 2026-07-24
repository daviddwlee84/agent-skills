# Plan: chordpro skill — faithful chord↔lyric alignment + music-theory progression validator

## Context

The `chordpro` skill already ships (author→eval→improve, 3 iterations). But charting
~10 C-pop songs surfaced two quality problems the user named directly: the
**chord-change timing vs. the lyrics** and the **overall chord progression** aren't
captured well.

Inspecting two real outputs pinpoints the cause — and it's an instruction written
*into* the skill, not a one-off slip:

- `~/Documents/chord-sheets/jay-chou-shuohao-buku/shuohao-buku.cho`, chorus:
  `眼看[G]著妳[B7]難過[Em7] [G/D] 挽[Cmaj7]留…沒有說[G] [D7]` — the `[G/D]`, `[G]`, `[D7]`
  are **floating** (sit over no syllable).
- `~/Documents/chord-sheets/li-ronghao-libai/li-ronghao-libai.cho`, verse 1:
  `[F]大部分人要我[F]學習… 世俗的[C]眼光[C]` — a **duplicate** `[F]…[F]` and a trailing `[C]`.

Root cause: `references/chord-tab-sources.md` steps 3–4 tell the agent to fetch
lyrics *separately* from LRCLIB, treat those as ground truth, and **re-align the
chart's chords onto them by eyeball** — discarding the one piece of ground-truth
alignment the chart already had (Chord4's `你不是真正(的)快樂` markup encodes exactly
which syllable each chord lands on). Floaters and duplicates are what fall out of a
lossy re-merge.

**Outcome of this change:** (1) preserve the source chart's own alignment via a
deterministic parser so the drift class disappears at the source; (2) add a
music-theory validator that detects the key, expresses every chord as a scale
degree (Roman + Nashville), and flags implausible/out-of-key chords via a
rock-corpus transition matrix — the user's "找調性 → 抓幾級和弦 → 定位簡易版 +
驗證和弦進行合理性" workflow, turned into a repeatable sanity gate.

Both research directions were confirmed by two Explore agents (Chord4/UG markup;
music-theory tooling). User chose the **Full + transition matrix** analyzer depth.

## Part A — Fix the alignment (Tier 1)

### A1. Reverse the re-merge instruction (skill content)
- Files: `references/chord-tab-sources.md` (steps 3–4), `SKILL.md` (the "Finding
  existing chord charts" section + the router row for a known song).
- New rule: **the chart's own (chord↔syllable) pairing is ground truth — preserve
  it.** LRCLIB is only for the synced `.lrc` sidecar and for filling lines a chart
  omits, never to re-align. Document two anti-patterns explicitly: no duplicate
  consecutive chords, no chords floating past the last syllable of a line
  (fold into an instrumental-bar `{comment}` or attach to the next downbeat).

### A2. New `scripts/chart-to-cho.py` (PEP 723 `uv run`; dep: `httpx`; optional `opencc`)
Deterministic fetch+parse of an existing chart → aligned inline ChordPro.
- **Chord4 (primary):** browser `User-Agent` + `Accept-Language` + `--compressed`
  (bare curl is Cloudflare-blocked). Extract the single `<pre>` inside
  `div.tabs_content`; **skip the header region** (credits + `Key=/Play=/Capo=` +
  the `Name  frets` fingering table) before the first chord/lyric pair; parse the
  body by **ordinal parenthesis-pairing** — Nth whitespace-split chord token
  (drop `|` bars) ↔ Nth `re.findall(r'\(([^)]*)\)')` marker; **detect instrumental
  lines** (lyric line has no CJK/word chars → emit chords bare with their bars,
  don't force pairing). Emit `[chord]syllable` preserving alignment — **no column
  math, no CJK double-width problem.** Pull `Key=`/`Play=`/`Capo=` into `{key}` /
  `{capo}` + a "sounds in <Play>" comment; standalone `[Word]` lines → `{comment}`.
  Simplified↔traditional is a URL variant (`/zh-hant/tabs/N` vs `/tabs/N`);
  `--opencc s2t|t2s` optional post-convert.
- **Ultimate Guitar (fallback):** regex `data-content="(.*?)"`, HTML-entity-unescape,
  `json.loads`, index `store.page.data.tab_view.wiki_tab.content`; inside each
  `[tab]…[/tab]` block do **positional ASCII-column mapping** of `[ch]C[/ch]`
  tokens over the lyric line (deterministic — all ASCII); capo/tonality from
  `tab_view.meta`.
- Interface: `--url <chart-url>` or `--html <file>`; `--site chord4|ug|auto`;
  `-o`; `--dry-run`; `--help`. Structured stdout (the `.cho`), diagnostics → stderr.
  Caption output with a `{comment}` naming the source + "published arrangement —
  verify against the recording (capo/key may differ)". **No** `AUTO-GENERATED`
  header (human-made chart, not machine ACR). Keep verbatim lyric handling
  personal-use.

### A3. Cleanup — folded into the analyzer (B1), not a third script
The parser emits clean output (preserving source alignment ⇒ no floaters/dups by
construction). The analyzer additionally *reports* duplicate-consecutive and
trailing-floating chords, covering charts built by other routes (`a2crd`,
interactive fill).

## Part B — Music-theory validator (Full + transition matrix)

### B1. New `scripts/analyze-progression.py` (PEP 723 `uv run`; **zero deps**; `music21` optional)
- **Input:** a `.cho` file (extract `[..]` chords in order, honoring section
  blocks) **or** `--key K --chords "C G Am F"`.
- **Pipeline:** chord-symbol parse (root + quality + `/bass` → pitch-class) →
  candidate-key scoring over 24 keys (`# diatonic − λ·circle-of-fifths-distance`
  for non-diatonic roots) → **relative maj/min disambiguation** via first/last
  chord + cadence weighting (the pitch-class set alone can't tell C from Am) →
  Roman + Nashville emission in the chosen key using **key-signature-aware letter
  spelling** (so `bVII` isn't mislabeled `#VI`) → per-chord diatonic-fit label
  {diatonic | borrowed | secondary | out-of-key} → **first-order transition
  scoring** against an inline rock-corpus-anchored Roman-numeral matrix → verdict.
- **Verdict output:** detected key + confidence (name the runner-up when
  relative/parallel is close); per-chord table `chord | Roman | Nashville | fit`;
  low-probability transition flags framed **"review — surprising, maybe
  intentional," not "wrong"**; **suspect list = the conjunction** (out-of-key AND
  reached by a rare move) → "likely mis-transcribed, double-check"; overall
  plausibility score; duplicate/floating-chord warnings; honesty footer.
- **Transition matrix:** hand-authored first-order Roman-numeral matrix
  (7×7 diatonic + a few chromatic rows: `bVII`, `V/V`), numbers **anchored to the
  de Clercq–Temperley Rock Corpus** (CC BY 4.0 — attribute it), NOT classical
  theory (rock legitimately does `V→IV`, `bVII→IV→I`; a classical prior over-flags).
  **Implementation note:** pull `rock_corpus_v2-1.zip` from rockcorpus.midside.com
  and aggregate, or lift the paper's published two-chord table — do **not**
  reconstruct the numbers from memory.
- **`music21` (optional, try-import / documented `--with music21`):** Krumhansl/
  Aarden key cross-check + reliable secondary-dominant analysis. Not required for
  the core to run; keeps the default lean and offline.

### B2. New `references/music-theory.md` (has a TOC)
Circle of fifths; diatonic-triad tables (major + natural/harmonic minor);
functional harmony (T / PD / D); common pop progressions; the key-fit scoring
recipe; the transition-matrix method + how to read the verdict; the
"find key → think in degrees → simplified version" workflow (matches the user's
relative-pitch mental model); honesty caveats (first-order prior can't see
voice-leading/modulation; rock-descriptive not prescriptive; relative maj/min
ambiguous; wrong key cascades into wrong numerals); the sources list from research.

### B3. Wire into the skill
- `SKILL.md`: add `analyze-progression.py` to the verify loop as a **non-blocking
  theory sanity-gate** (after building a `.cho`, run it; many out-of-key/low-prob
  flags ⇒ re-check the chart or the key) and as a **tie-breaker** in the
  cross-check note; add both new scripts to **Available scripts**; add
  `chart-to-cho.py` to the chart-fetch recipe; update **Gotchas** (preserve source
  alignment; duplicate/floating chords); add `references/music-theory.md` to the
  **Reference files** list.
- `references/chord-tab-sources.md`: replace the hand-parse steps (3–4) with
  "run `chart-to-cho.py`"; keep the markup documentation as the parser's spec.
- `references/lyrics-sources.md`: one line noting LRCLIB is the `.lrc` sidecar /
  gap-filler when an aligned chart exists, not the alignment source.

## Files touched
- **New:** `skills/local/chordpro/scripts/chart-to-cho.py`,
  `skills/local/chordpro/scripts/analyze-progression.py`,
  `skills/local/chordpro/references/music-theory.md`
- **Edit:** `skills/local/chordpro/SKILL.md`,
  `skills/local/chordpro/references/chord-tab-sources.md`,
  `skills/local/chordpro/references/lyrics-sources.md`
- **No** `marketplace.json` change (skill already registered under `music-notation`).

## Verification
1. **Lint:** `bash skills/local/skill-author/scripts/lint-skill.sh skills/local/chordpro`
   (SKILL.md < 500 lines — watch the budget as mentions grow; refs reachable;
   every script answers `--help`).
2. **Parser fidelity:** `uv run scripts/chart-to-cho.py --url https://chord4.com/zh-hant/tabs/30689 -o /tmp/shuohao.cho`;
   diff its alignment against the current hand-made
   `shuohao-buku.cho` — confirm **no floaters/duplicates**, and that `{key}`/`{capo}`
   were extracted. Repeat on one UG song via `--site ug`.
3. **Parse + render:** `scripts/validate-cho.sh /tmp/shuohao.cho` and
   `scripts/render-cho.sh /tmp/shuohao.cho` (parses + CJK renders, no tofu).
4. **Analyzer:** `uv run scripts/analyze-progression.py /tmp/shuohao.cho` → sensible
   key (G, capo-relative), degree table, plausible flags. Run it on the existing
   `li-ronghao-libai.cho` and `shuohao-buku.cho` and confirm it **catches the real
   `[F]…[F]` duplicate and the trailing `[D7]` floater**, and labels `F#m7` /
   `Em/C#` correctly. Confirm it runs **zero-dep** (no network, no music21).
5. **Script hygiene:** `--dry-run` and `--help` on both new scripts.
6. **End-to-end (optional):** re-chart one song fetch→parse→analyze→render to
   sanity-check the whole revised flow before touching the batch.
