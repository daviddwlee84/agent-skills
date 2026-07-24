# Finding existing chord charts online

Read this when the user wants chords for a **known/popular song** (by title, by
lyrics, or from a link) and hasn't pasted chords or supplied audio. For most
songs people ask about, **a human-made chart already exists on the web** — and it
is usually *more accurate* than machine audio→chord extraction (`audio-to-chords.py`,
~80%). So the reliable first move is: search chart sites → adapt the chart to
ChordPro → validate. Fall back to audio ACR or interactive fill only when no
chart is found.

This is the router's highest-value path for "make me a chord sheet for `<song>`",
and it's what actually happens in practice — treat existing charts as the
default source of chords, not an afterthought.

## The workflow

Verified across a 7-song C-pop batch — the naive "WebFetch → a2crd" path breaks in
two ways (WebFetch's summarizer strips copyrighted lyrics; `a2crd` mis-aligns CJK).
The reliable recipe uses **`scripts/chart-to-cho.py`**, which fetches + parses a
chart and **preserves the chart's own chord-to-syllable alignment** — the single
most important property. A chart already encodes which syllable each chord sits on
(Chord4's `後來的生(活)` markup, UG's monospace columns); the script reproduces that
exactly. **Do not re-align fetched chords onto separately-fetched lyrics by eye** —
that lossy re-merge is what produces drifted/floating/duplicated chords.

1. **Search.** `WebSearch` for the song + a chart keyword in the right language:
   - EN: `"<artist> <title>" chords`, `... ultimate guitar`, `... chordpro`
   - 中文: `<歌手> <歌名> 吉他谱`, `... 和弦`, `... 弹唱谱`, `... 简谱`
2. **Convert with `chart-to-cho.py`** (it fetches with a browser UA, parses the
   site markup, and keeps the alignment):

   ```bash
   uv run scripts/chart-to-cho.py --url <chart-url> -o song.cho     # Chord4 or UG
   uv run scripts/chart-to-cho.py --site ug --url <ug-url> -o song.cho
   # Cloudflare challenge? open the URL in a browser, save the page, then:
   uv run scripts/chart-to-cho.py --html saved.html --site chord4 -o song.cho
   ```

   It auto-detects Chord4 vs Ultimate Guitar, pulls title/artist and (Chord4)
   `Key=/Play=/Capo=` metadata, and captions the source. **Chord4 is primary** for
   Mandarin; UG is the fallback. For an **image-only 六线谱** (jitahome/qinhun/…)
   there is no text to parse and the script can't help — `WebFetch` will *fabricate*
   placement, so transcribe manually from an explicit chord **list** only.
3. **The chart's alignment is ground truth — keep it.** `chart-to-cho.py` already
   preserved it. Use **LRCLIB only** for the time-synced **`.lrc` sidecar** and to
   **fill lines the chart omits** — never to re-align chords that the chart already
   placed:

   ```bash
   uv run scripts/fetch-lyrics.py --artist "…" --track "…" -o song.lrc   # sidecar only
   ```

   (LRCLIB text arrives traditional or simplified; use `--opencc` on `chart-to-cho.py`
   if you need to match a variant — see below.) If the chart omits an intro/interlude,
   reuse the relevant verse loop labeled "verify against recording" — never fabricate
   a specific riff.
4. **Sanity-check the harmony** with `scripts/analyze-progression.py song.cho`: it
   detects the key, labels every chord by scale degree, and flags out-of-key +
   improbable-move chords (likely mis-transcriptions) plus duplicate/floating chords.
   See `references/music-theory.md`. Use it as a **tie-breaker** when two charts
   disagree — prefer the one with higher plausibility / fewer suspects.
5. **Validate AND render.** `scripts/validate-cho.sh` (parse) **and**
   `scripts/render-cho.sh` (CJK-safe render + glyph-check — a bare `chordpro -o`
   renders Chinese as tofu yet passes validation). The source `{comment:}` caption is
   added by `chart-to-cho.py`. Human-made chart, not machine ACR — so no
   `AUTO-GENERATED` header.

**When the script needs a hand.** `chart-to-cho.py` covers the two dominant markups;
the site-specific structure it relies on is documented below, so you can adjust the
parser or hand-transcribe an oddball chart. The mechanics: **Chord4** = one `<pre>`
in `div.tabs_content`, ordinal parenthesis-pairing (Nth chord token ↔ Nth `(字)`
marker, `|` bars ignored), instrumental lines are marker-only `( )`; **Ultimate
Guitar** = `js-store` `data-content` JSON → `tab_view.wiki_tab.content`, monospace
ASCII columns of `[ch]C[/ch]` over the lyric line. `chordpro --a2crd` remains an
option for **pure-Latin** chords-over-lyrics, but its 1-char = 1-column heuristic
drifts on full-width CJK — the parser sidesteps that entirely.

## Where the charts live

Coverage and format vary; try a couple, and **don't rely on any single site**
(the batch hit `kanpu8` HTTP 403 and `jitapai` expired-TLS). Auto-generated sites
are effectively ACR — same ~80% caveat.

**Chinese / Taiwan (great for C-pop like the 落葉歸根 case):**
- **Chord4 / 和弦网** — `chord4.com` — **the repeat winner** (sourced chords in 6 of 7
  eval runs). Raw HTML exposes a parseable chords-over-lyrics block. Start here for Mandarin.
- **91譜 / 91pu** — `91pu.com.tw` — large Taiwan library, but **JS-rendered**; `curl`
  often returns only page chrome. Good to eyeball, awkward to parse.
- **弹唱谱 / 简谱 hubs** — `qupu123`, `中国曲谱网 (qupu.com)`, `17jita`, `jitaba/jitapu`,
  `jitahome`, `qinhun`, `guistudy` — **mostly image 六线谱** (manual transcription);
  simplified-character search finds more.
- **魔鏡歌詞 / Mojim** — `mojim.com` — mostly lyrics, some chords; good for confirming lyrics.

**Western / global:**
- **Ultimate Guitar** — `ultimate-guitar.com` — largest, but **fully JS-rendered**;
  `WebFetch` returns no chords. Parse the `js-store` `data-content` JSON from raw HTML.
- **e-chords**, **Chordie**, **AZChords** — chords-over-lyrics, usually parseable.
- **Songsterr** — public API for tabs/chords (`songsterr.com/a/wsa/api-tabs-a26570`).
- **Chordu / Chordify / GuitarTuna** — **auto-generated from audio** → ACR-quality
  (~80%, verify), not human-checked. Use only to corroborate.

## Format taxonomy (what you'll get back)

| Format | How to use it | Reliability |
|---|---|---|
| Latin chords-over-lyrics text | `chordpro --a2crd` → clean up → validate | High (human-made) |
| CJK chords-over-lyrics text | hand-align by phrase (a2crd drifts on full-width) → validate | High |
| Inline / chord chart | transcribe into the ChordPro template | High |
| Guitar tab (6-line) | embed in a `{start_of_tab}` block; or use for riffs only | High for riffs |
| 简谱 (numbered) / image scan | manual transcription; no reliable OMR — trust only an explicit chord list | Low (tedious) |
| Auto-generated (chordu/chordify) | same as ACR — a draft to verify | ~80% |

## Simplified vs traditional, and the metadata a chart won't give you

- **Char-set mismatch is common**: a simplified-character chart vs a traditional-character
  preference (or vice versa). The **chart is the source of alignment** — keep its own
  chord↔syllable pairing. If you want the other character set, pick the Chord4 URL
  variant (`/zh-hant/tabs/N` = traditional, `/tabs/N` = simplified) or run
  `chart-to-cho.py --opencc t2s|s2t`; `opencc` converts the *characters* while the
  chord placement (position-based) is unaffected. Reach for LRCLIB only to fill lines
  the chart is missing.
- **capo / tempo / composer / year** are usually **absent from text charts**. Get them
  from a second source (Wikipedia/Baidu/SongBPM), but **tempo is unreliable** — beware
  the half-time trap (a song *felt* at 82 BPM is often listed as 164). Omit an unknown
  field or caption it "unverified"; never fabricate.

## Legality (surface it, don't bury it)

These charts are user-contributed arrangements; the underlying songs are usually
copyrighted. Keep it **personal-use and local**, don't redistribute the fetched
chart or lyrics commercially, and cite the source in a `{comment:}`. Prefer this
route over downloading audio — it avoids the platform-ToS problem entirely — but
the copyright of the song itself still applies to any lyrics you embed.
