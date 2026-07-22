# Lyrics sources: synced vs plain, API vs scrape, legality

Read this when fetching lyrics to fill a chord sheet. **Default to LRCLIB** — the
only source that is free, key-less, cross-platform, and returns time-synced
`.lrc`. `scripts/fetch-lyrics.py` uses it. Everything else has a catch (paid,
partner-gated, or scrape-only with ToS risk).

## Source table

| Source | Access | Time-synced `.lrc`? | Notes |
|---|---|---|---|
| **LRCLIB** | **Free, open, no key** | **Yes** — line-level `syncedLyrics` + `plainLyrics` | Best first choice. Community-contributed → coverage patchy for niche/Chinese/live tracks. Wrappers: `lrclib-api` |
| **Musixmatch** | Dev API (**key required**) | Yes — line-level `subtitle` + word-level `richsync` | Free tier returns only a **30% preview**; full/synced needs a **paid commercial license**. Unofficial scrapers (MxLRC) violate ToS |
| **Genius** (`lyricsgenius`) | Free API token for search/metadata; **API returns no lyrics** — the lib **scrapes the page HTML** | **No** — plain text only | Great English coverage; Py ≥3.11, actively maintained |
| **Mojim / 魔鏡歌詞** | **Scrape-only** (community datasets, e.g. `ecrows/mojim-lyrics`) | **No** — plain text | Large Mandarin/Cantonese DB; ToS/copyright caution |
| **KKBOX** | Open/Partner API | In-app yes, but **lyrics gated behind partner licensing** | Effectively partner-only for lyrics |
| **NetEase Cloud Music** | Unofficial community APIs (`NeteaseCloudMusicApi` + Py wrappers) | **Yes** — line-level `.lrc` (+ translations) | Excellent for Chinese songs; unofficial → ToS risk |
| **QQ Music** | Community tools (`QRCD`, `qqmusic-api-python`) | **Yes** — but proprietary encrypted **KRC** needing decryption | Word-level timing available; more reverse-engineering; unofficial → ToS risk |

**Synced `.lrc` available**: LRCLIB (free), Musixmatch (paid), NetEase
(unofficial), QQ (unofficial, decrypt). **Plain only**: Genius, Mojim.
**Partner-gated**: KKBOX.

## LRCLIB API (what `fetch-lyrics.py` calls)

No key. Two endpoints:

```
# Exact-ish match (best when you know duration; duration match is fuzzy ±)
GET https://lrclib.net/api/get?artist_name=<a>&track_name=<t>&album_name=<al>&duration=<sec>

# Search (fallback when /get misses)
GET https://lrclib.net/api/search?q=<free text>            # or &artist_name=&track_name=
```

Response fields: `syncedLyrics` (LRC with `[mm:ss.xx]` timestamps), `plainLyrics`,
`instrumental` (bool), plus `trackName`/`artistName`/`albumName`/`duration`.
Send a descriptive `User-Agent` (the project asks for one). Missing tracks return
404 on `/get` — fall back to `/search` and pick the closest by duration.

**CJK titles**: `/get` is brittle for Chinese/Japanese/Korean metadata — an exact
Han query often 404s and `/search` can miss too. Retry with the **romanized/pinyin**
artist+title (e.g. `Li Ronghao` / `Li Bai`, `Mayday`): LRCLIB frequently indexes the
romanized name and still returns the CJK lyrics. `fetch-lyrics.py` does this retry
automatically, but the pattern is worth knowing when querying by hand.

## How synced lyrics feed a chord sheet

- **Line-synced `.lrc`** gives per-line timestamps. Combined with the chord
  timeline from ACR, you can place chords at **line** granularity (the chord
  changes nearest each line's start). This is the realistic target.
- **Word-level** placement (a chord over an exact syllable) needs word-level
  lyric timing — only Musixmatch `richsync` or QQ KRC provide it. Without it, put
  chords at line starts and let the user nudge them.
- **Plain text only** (Genius/Mojim): no timing. Either place chords manually /
  interactively, or run forced alignment (WhisperX) against the audio to recover
  line timing first.

## Legality

- **LRCLIB** is the safe default (open, community). Prefer it.
- Genius/Mojim scraping and the unofficial NetEase/QQ/Musixmatch routes carry
  **ToS and copyright risk** — keep usage personal, local, non-redistributed, and
  tell the user when a path relies on scraping rather than an official API.
- Don't ship a scraper in this skill; document these as manual options the user
  can pursue with their own judgment.

## Selected sources

- LRCLIB: https://lrclib.net/ · server https://github.com/tranxuanthang/lrclib
- Musixmatch SDK: https://github.com/musixmatch/musixmatch-sdk
- lyricsgenius: https://pypi.org/project/lyricsgenius/
- Mojim dataset: https://github.com/ecrows/mojim-lyrics
- NetEase endpoints: https://github.com/Binaryify/NeteaseCloudMusicApi ·
  QQ KRC tool: https://github.com/xmcp/QRCD
