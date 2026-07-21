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

1. **Search.** `WebSearch` for the song + a chart keyword in the right language:
   - EN: `"<artist> <title>" chords`, `... ultimate guitar`, `... chordpro`
   - 中文: `<歌手> <歌名> 吉他谱`, `... 和弦`, `... 弹唱谱`, `... 简谱`
2. **Fetch.** `WebFetch` the most promising result and pull the **chords-over-lyrics**
   block (chord symbols on their own line above each lyric line).
3. **Adapt.** If it's chords-over-lyrics text, run it through `chordpro --a2crd`
   (see `cli-and-rendering.md`) — that's exactly its input format. If it's already
   inline or a chart, transcribe it into the ChordPro template.
4. **Validate + caption.** Run `scripts/validate-cho.sh`. Add a `{comment:}` noting
   the source and that it's a *published arrangement to verify against the
   recording* (capo/key can differ between charts). Do **not** stamp the
   machine-extraction `AUTO-GENERATED` header — this isn't ACR — but do stay honest
   that a web chart is one person's arrangement, not ground truth.

## Where the charts live

Coverage and format vary; try a couple. **Text (chords-over-lyrics)** sites feed
straight into `a2crd`; **image** charts (many 吉他谱/简谱 scans) need manual
transcription (no reliable OMR). Auto-generated sites are effectively ACR — same
~80% caveat.

**Chinese / Taiwan (great for C-pop like the 落葉歸根 case):**
- **91譜 / 91pu** — `91pu.com.tw` — large Taiwan library of ready 吉他谱/弹唱谱; often the fastest hit for Mandarin songs.
- **Chord4 / 和弦网** — `chord4.com` — chords-over-lyrics, capo/key noted (used by the eval runs).
- **弹唱谱 / 简谱 hubs** — `kanpu8`, `qupu123`, `中国曲谱网 (qupu.com)`, `17jita (17吉他网)`, `jitaba/jitapu` — mix of text and image; simplified-character search often finds more.
- **魔鏡歌詞 / Mojim** — `mojim.com` — mostly lyrics, some chords; good for confirming lyrics.

**Western / global:**
- **Ultimate Guitar** — `ultimate-guitar.com` — the largest; use the **"Chords"** tab (chords-over-lyrics) not "Tab". No official API; scrape the page.
- **e-chords**, **Chordie**, **AZChords** — chords-over-lyrics.
- **Songsterr** — public API for tabs/chords (`songsterr.com/a/wsa/api-tabs-a26570`).
- **Chordu / Chordify / GuitarTuna** — **auto-generated from audio** → treat as ACR-quality (~80%, verify), not human-checked.

## Format taxonomy (what you'll get back)

| Format | How to use it | Reliability |
|---|---|---|
| Chords-over-lyrics text | `chordpro --a2crd` → clean up → validate | High (human-made) |
| Inline / chord chart | transcribe into the ChordPro template | High |
| Guitar tab (6-line) | embed in a `{start_of_tab}` block; or use for riffs only | High for riffs |
| 简谱 (numbered) / image scan | manual transcription; no reliable OMR | Low (tedious) |
| Auto-generated (chordu/chordify) | same as ACR — a draft to verify | ~80% |

## Legality (surface it, don't bury it)

These charts are user-contributed arrangements; the underlying songs are usually
copyrighted. Keep it **personal-use and local**, don't redistribute the fetched
chart or lyrics commercially, and cite the source in a `{comment:}`. Prefer this
route over downloading audio — it avoids the platform-ToS problem entirely — but
the copyright of the song itself still applies to any lyrics you embed.
