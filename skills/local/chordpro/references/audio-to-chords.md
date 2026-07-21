# Audio / link → chords: feasibility, tools, and honest limits

Read this when the user wants chords from an audio file or a
YouTube/Bilibili/SoundCloud link. **The headline: this is a draft generator,
not a transcriber.** Set that expectation before running anything.

## Accuracy reality — say this out loud

Open automatic chord recognition (ACR) at the current state of the art (MIREX
2024/2025 Audio Chord Estimation) tops out around **78–80% WCSR on major/minor**,
dropping to the **mid-60s% for sevenths**. Models "excel on frequent major/minor
chords but underperform on rare seventh and extended chords." So even on simple
pop, roughly **1 second in 5 is mislabeled**; jazz, modulations, quiet intros,
and dense mixes are much worse, and **inversions / slash chords are unreliable**.
The tool also outputs *absolute* pitches — it cannot know the capo a guitarist
used. Every machine-extracted sheet ships with a
`{comment: AUTO-GENERATED — verify chords/key/timing}` header.

## The pipeline

```
link ─▶ yt-dlp (→ wav)
        └▶ [optional] Demucs stem separation (isolate harmonic content — can help ACR)
        ─▶ ACR (chord-extractor/Chordino | madmom CNN | Omnizart) ─▶ chord timeline (.lab)
        ─▶ beats/downbeats (madmom) + key (Essentia/librosa) ─▶ bar grid + key/tempo
lyrics ─▶ LRCLIB (synced) ─first── else ─▶ Musixmatch ─ else ─▶ scrape/plain
        └▶ if PLAIN only: forced alignment (WhisperX) to recover line timing
merge  ─▶ snap chord onsets to beats; place [Chord] at nearest change per lyric line
output ─▶ ChordPro draft with AUTO-GENERATED header + {key}/{tempo}
```

`scripts/audio-to-chords.py` automates the download → ACR → skeleton portion and
degrades gracefully when the ACR backend is missing.

## Getting audio: `yt-dlp`

Supports **YouTube, SoundCloud, AND Bilibili** (1000+ sites). Needs **ffmpeg**
for `-x` audio extraction.

```bash
# best audio -> wav (best for analysis); swap wav->mp3 for MP3
yt-dlp -x --audio-format wav --audio-quality 0 -o "%(title)s.%(ext)s" "URL"
```

- **Bilibili**: public videos work; higher-res/member content needs
  `--cookies-from-browser chrome`.
- **SoundCloud**: public tracks work; some are download-disabled/private.
- **Legal/ToS**: downloading copyrighted audio generally violates the platform's
  ToS and can infringe copyright. Frame as **personal-use, user-owns-or-has-rights**,
  process **locally**, **don't redistribute**. Surface this to the user.

## ACR tools (audio → time-stamped chords)

| Tool | Status (2026) | Invoke | Vocab | When to pick |
|---|---|---|---|---|
| **chord-extractor** (ohollo) | Maintained (v0.1.3, Aug 2025); wraps **Chordino** | `pip install chord-extractor`; `Chordino(roll_on=1).extract('song.wav')` | maj/min + some 7ths | **Default.** Turnkey on Linux; on macOS/Windows needs a Vamp plugin pack + `VAMP_PATH` (the friction point) |
| **madmom** CNN | NN models are best-in-class but install is painful (classifiers cap at Py 3.7; use 3.8–3.9 or the `imcmurray/madmom-modern` fork) | `CNNChordFeatureProcessor` + `CRFChordRecognitionProcessor` | maj/min | Higher accuracy when you can pin the env; also gives **beats/downbeats** |
| **Omnizart** | Actively maintained; Docker; Py ≥3.8; heavy (TF + fluidsynth) | `omnizart download-checkpoints` → `omnizart chord transcribe in.wav` | richer | Heavyweight multitask toolbox (also drums/melody/vocal) |
| **Chordino / NNLS-Chroma** (Vamp) | Mature C++; the engine under the above | `sonic-annotator -d vamp:nnls-chroma:chordino:simplechord in.wav -w csv` | maj/min + basic 7ths | Cross-platform CLI baseline without Python glue |
| **autochord** | Effectively frozen (last release 2021; TF-1.x rot) | `pip install autochord`; `autochord.recognize('a.wav','chords.lab')` | **25: 12 maj + 12 min + N only** | Only if others fail; major/minor only |
| **Hugging Face** | Research/demo-grade; **no stable plug-and-play audio→chord model** | Spaces like `tigorsinaga/AI_CHORD_RECOGNITION`; repos `chord-engine`, `Audio-Chord-Recognition` | varies | Mention as "cutting edge", don't depend on it. (`musiclang` is *symbolic* generation, not audio→chord) |

**macOS note**: `chord-extractor`'s bundled Chordino binary is Linux-only. On
macOS you must install the NNLS-Chroma Vamp plugin and set `VAMP_PATH`, OR fall
back to `sonic-annotator` with the plugin, OR run in a Linux container. The
script detects the missing plugin and prints this guidance.

## Beat / downbeat + key (complements chords)

- **madmom** — best NN **beat/downbeat** (`RNNDownBeatProcessor` +
  `DBNDownBeatTrackingProcessor`); downbeats give the bar grid to snap chords to.
- **librosa** — pure-Python, trivial install: `librosa.beat.beat_track` (tempo +
  beats); chroma for a hand-rolled Krumhansl-Schmuckler key estimate.
- **Essentia** — `KeyExtractor` (key+scale), `RhythmExtractor2013`; heavier install.
- **KeyFinder** — desktop GUI, not a library (`libKeyFinder` C++ if binding).

**Key caveat**: detection is ~70–90% and confuses relative major/minor and
keys a fifth apart. Treat detected key as a *suggestion*; confirm with the user.

## Where it breaks (tell the user)

1. Chord accuracy (~80% simple pop; worse on 7ths/jazz/modulation/quiet/dense).
2. Chord↔lyric alignment — chords are timestamped; mapping to the exact *syllable*
   needs word-level lyric timing (rare — Musixmatch richsync / QQ KRC). Most
   drafts land chords at **line** granularity; a human nudges them.
3. Capo/key ambiguity + enharmonic spelling.
4. Vocabulary mismatch (maj/min-only tools oversimplify sus/add/7 songs).
5. Lyrics coverage gaps for niche/Chinese/live tracks → scrape or ASR fallback.

## Commercial / reference escape hatches (name-drop only)

- **Moises** — real developer/extensions platform (`extensions.moises.ai`,
  request access): stems, chords, beat. The one with genuine API access.
- **Songsterr** — public API for tabs/chords (CORS-restricted → server-side).
- **Chordify** — no official public API.
- **Chord AI** — explicitly no API.
- **Ultimate Guitar** — no official public API (third-party scrapers only).

## Selected sources

- chord-extractor: https://github.com/ohollo/chord-extractor
- madmom chords: https://madmom.readthedocs.io/en/v0.16/modules/features/chords.html ·
  modern fork https://github.com/imcmurray/madmom-modern
- Omnizart: https://github.com/Music-and-Culture-Technology-Lab/omnizart
- NNLS-Chroma / Chordino: https://isophonics.net/nnls-chroma.html
- MIREX ACE results: https://www.music-ir.org/mirex/wiki/2025:Audio_Chord_Estimation_Results
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- Moises API: https://extensions.moises.ai/api-reference · Songsterr API:
  https://www.songsterr.com/a/wsa/api-tabs-a26570
