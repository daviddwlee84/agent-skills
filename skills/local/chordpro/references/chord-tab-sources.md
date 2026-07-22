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
two ways (WebFetch's summarizer strips copyrighted lyrics; `a2crd` mis-aligns CJK),
so the real recipe is:

1. **Search.** `WebSearch` for the song + a chart keyword in the right language:
   - EN: `"<artist> <title>" chords`, `... ultimate guitar`, `... chordpro`
   - 中文: `<歌手> <歌名> 吉他谱`, `... 和弦`, `... 弹唱谱`, `... 简谱`
2. **Fetch RAW, then parse the site's markup.** `WebFetch`'s LLM summary **strips the
   copyrighted lyrics** (returns "[歌词已移除]" / "[lyrics omitted]"), so you get chords
   with no alignment. Instead `curl -sL <url>` the raw HTML and parse the site markup:
   - **Chord4** (best for Mandarin): chords are parenthesized syllables like
     `你不是真正(的)快樂` (chord sits above the `(char)`), plus `data-chord` attrs,
     inside the `tabs_content` `<pre>` block.
   - **Ultimate Guitar**: JS-rendered — the chart is in the embedded **`js-store`
     `data-content` JSON** as `[ch]C[/ch] … [tab]…[/tab]`.
   - **Image-only 六线谱** (common for C-pop — jitahome/qinhun/guistudy…): there is NO
     text to parse. `WebFetch` will *confidently fabricate* per-line placement — trust
     only an explicit chord **list**, never fabricated alignment.
3. **Lyrics come SEPARATELY from LRCLIB** (`scripts/fetch-lyrics.py -o song.lrc`).
   Treat LRCLIB lyrics as ground truth (they arrive traditional or simplified —
   see below).
4. **Align by phrase, not by column.** `chordpro --a2crd` only works on **pure-Latin**
   chords-over-lyrics; for CJK its 1-char = 1-column heuristic drifts (full-width
   chars are 2 display cells). Place each chord over the syllable/phrase it belongs
   to by musical judgment. If the chart omits an intro/interlude, reuse the relevant
   verse loop labeled "verify against recording" — never fabricate a specific riff.
5. **Validate AND render.** `scripts/validate-cho.sh` (parse) **and**
   `scripts/render-cho.sh` (CJK-safe render + glyph-check — a bare `chordpro -o`
   renders Chinese as tofu yet passes validation). Caption a `{comment:}` naming the
   source + "published arrangement — verify against the recording (capo/key may
   differ)". Not machine ACR, so no `AUTO-GENERATED` header.

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

- **Char-set mismatch is common**: a simplified-character chart vs traditional LRCLIB
  lyrics (or vice versa). Treat the **LRCLIB lyrics as ground truth** and map chords by
  position/meaning, not string equality. `opencc` can convert if you must reconcile.
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
