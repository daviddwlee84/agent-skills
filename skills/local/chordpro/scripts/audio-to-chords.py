#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "yt-dlp>=2024.1",
# ]
# ///
"""audio-to-chords.py — best-effort link/audio -> DRAFT ChordPro.

This is a draft generator, NOT a transcriber. Open automatic chord recognition
tops out around ~80% on simple major/minor pop and is worse on 7ths, jazz, key
changes, and dense mixes; the detected key is a suggestion, and inversions/slash
chords are unreliable. Output always carries an AUTO-GENERATED header — a human
must verify chords, key, and timing. See references/audio-to-chords.md.

Pipeline: URL --(yt-dlp)--> wav --(chord-extractor/Chordino)--> chord timeline
--> ChordPro skeleton. If an .lrc is supplied (--lrc), chords are placed at line
granularity onto the lyric lines.

    uv run audio-to-chords.py --dry-run "https://youtu.be/..."
    uv run audio-to-chords.py -o draft.cho "https://youtu.be/..."
    uv run audio-to-chords.py --lrc song.lrc --title "Hello" song.wav -o draft.cho

LEGAL: only process content you own or have the right to use, for personal use,
locally. Downloading copyrighted audio can violate a platform's Terms of Service.

The ACR backend (chord-extractor + the Chordino Vamp plugin) is NOT a declared
dependency because its native plugin doesn't install cleanly everywhere
(notably macOS). If it's missing, this script downloads the audio, tells you the
wav path, prints exact install guidance, and exits — it degrades, it doesn't
crash.

Exit codes:
  0  draft ChordPro emitted
  1  invalid arguments
  2  input not found
  3  ACR backend unavailable (audio may still have been downloaded — see stderr)
  4  audio download / decode failure
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

LRC_TS = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def log(msg: str) -> None:
    """Diagnostics -> stderr."""
    print(msg, file=sys.stderr)


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audio-to-chords.py",
        description="Best-effort link/audio -> draft ChordPro (yt-dlp + chord-extractor).",
        epilog=(
            "Examples:\n"
            '  uv run audio-to-chords.py --dry-run "https://youtu.be/dQw4w9WgXcQ"\n'
            "  uv run audio-to-chords.py -o draft.cho song.wav\n"
            '  uv run audio-to-chords.py --lrc song.lrc --title "Hello" song.wav\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", help="A URL (YouTube/Bilibili/SoundCloud) or a local audio file.")
    p.add_argument("-o", "--output", help="Write ChordPro here instead of stdout.")
    p.add_argument("--lrc", help="Optional .lrc (synced lyrics) to align chords onto.")
    p.add_argument("--title", help="Song title for the {title:} directive.")
    p.add_argument("--artist", help="Artist for the {artist:} directive.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan (no download, no analysis), then exit.",
    )
    return p


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def download_audio(url: str, outdir: Path) -> tuple[Path, dict]:
    """Download bestaudio and convert to wav via yt-dlp + ffmpeg."""
    import yt_dlp  # declared dependency

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(outdir / "%(title)s.%(ext)s"),
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "wav"}
        ],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        base = Path(ydl.prepare_filename(info))
    wav = base.with_suffix(".wav")
    if not wav.exists():
        # Fall back to whatever the postprocessor produced.
        candidates = sorted(outdir.glob("*.wav"))
        if candidates:
            wav = candidates[0]
    return wav, info


def extract_chords(wav: Path) -> list[tuple[float, str]]:
    """Run chord-extractor/Chordino. Raises RuntimeError with guidance if the
    backend isn't usable, so main() can degrade gracefully."""
    try:
        from chord_extractor.extractors import Chordino
    except ImportError as exc:
        raise RuntimeError(
            "chord-extractor is not installed.\n"
            "  Install (Linux, turnkey):  uv pip install chord-extractor\n"
            "  macOS/Windows also need the NNLS-Chroma Vamp plugin + VAMP_PATH,\n"
            "  or use `sonic-annotator` / a Linux container.\n"
            "  Details: references/audio-to-chords.md"
        ) from exc

    try:
        chordino = Chordino(roll_on=1)
        raw = chordino.extract(str(wav))
    except Exception as exc:  # Vamp plugin missing at runtime, decode error, etc.
        raise RuntimeError(
            f"Chordino failed to analyze the audio ({exc}).\n"
            "  This usually means the NNLS-Chroma Vamp plugin isn't installed or\n"
            "  VAMP_PATH isn't set. See references/audio-to-chords.md for setup,\n"
            "  or run `sonic-annotator -d vamp:nnls-chroma:chordino:simplechord`\n"
            "  on the wav manually."
        ) from exc

    changes: list[tuple[float, str]] = []
    for item in raw:
        chord = getattr(item, "chord", None)
        ts = getattr(item, "timestamp", None)
        if chord is None and isinstance(item, (list, tuple)) and len(item) >= 2:
            chord, ts = item[0], item[1]
        if chord is None:
            continue
        changes.append((float(ts or 0.0), str(chord)))
    changes.sort(key=lambda c: c[0])
    return changes


def dedupe(changes: list[tuple[float, str]]) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    for ts, ch in changes:
        if not out or out[-1][1] != ch:
            out.append((ts, ch))
    return out


def chord_at(t: float, changes: list[tuple[float, str]]) -> str | None:
    cur: str | None = None
    for ts, ch in changes:
        if ts <= t:
            cur = ch
        else:
            break
    if cur in (None, "N", "NC", "N.C."):
        return None
    return cur


def parse_lrc(text: str) -> list[tuple[float, str]]:
    lines: list[tuple[float, str]] = []
    for raw in text.splitlines():
        stamps = LRC_TS.findall(raw)
        content = LRC_TS.sub("", raw).strip()
        for mm, ss in stamps:
            lines.append((int(mm) * 60 + float(ss), content))
    lines.sort(key=lambda x: x[0])
    return lines


def mmss(t: float) -> str:
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def build_chordpro(
    changes: list[tuple[float, str]],
    lrc_text: str | None,
    title: str | None,
    artist: str | None,
) -> str:
    changes = dedupe(changes)
    out: list[str] = []
    if title:
        out.append(f"{{title: {title}}}")
    if artist:
        out.append(f"{{artist: {artist}}}")
    out.append("{comment: AUTO-GENERATED — verify chords/key/timing}")
    out.append("")

    if lrc_text:
        lyric_lines = parse_lrc(lrc_text)
        if lyric_lines:
            out.append("{start_of_verse}")
            for t, content in lyric_lines:
                ch = chord_at(t, changes)
                prefix = f"[{ch}]" if ch else ""
                out.append(f"{prefix}{content}" if content else (prefix or ""))
            out.append("{end_of_verse}")
            out.append("")

    # Always include the raw chord timeline so the user can correct placement.
    out.append("{comment: Detected chord timeline (mm:ss → chord)}")
    out.append("{start_of_tab}")
    if changes:
        for t, ch in changes:
            out.append(f"{mmss(t)}  {ch}")
    else:
        out.append("(no chords detected)")
    out.append("{end_of_tab}")
    out.append("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)

    src_is_url = is_url(args.input)
    if not src_is_url and not Path(args.input).exists():
        log(f"input not found: {args.input}")
        return 2

    if args.dry_run:
        log("[dry-run] plan:")
        if src_is_url:
            log(f"  1. yt-dlp download bestaudio -> wav  ({args.input})")
        else:
            log(f"  1. use local audio file  ({args.input})")
        log("  2. chord-extractor/Chordino -> chord timeline")
        if args.lrc:
            log(f"  3. align chords onto lyric lines from {args.lrc}")
        log("  4. emit ChordPro with AUTO-GENERATED header")
        log("Reminder: personal-use / local only; respect platform ToS + copyright.")
        return 0

    tmpdir = Path(tempfile.mkdtemp(prefix="chordpro-audio-"))
    if src_is_url:
        log(f"downloading audio with yt-dlp -> {tmpdir} …")
        try:
            wav, info = download_audio(args.input, tmpdir)
        except Exception as exc:  # DownloadError, missing ffmpeg, etc.
            log(f"audio download failed: {exc}")
            log("Ensure yt-dlp and ffmpeg are available; some tracks are gated "
                "(try --cookies-from-browser via yt-dlp directly).")
            return 4
        if not args.title:
            args.title = info.get("track") or info.get("title")
        if not args.artist:
            args.artist = info.get("artist") or info.get("uploader")
        log(f"audio: {wav}")
    else:
        wav = Path(args.input)

    try:
        changes = extract_chords(wav)
    except RuntimeError as exc:
        log(str(exc))
        log(f"The audio is available at: {wav}")
        return 3

    log(f"detected {len(dedupe(changes))} chord changes")

    lrc_text = None
    if args.lrc:
        lrc_path = Path(args.lrc)
        if not lrc_path.exists():
            log(f"--lrc file not found: {args.lrc} (continuing without lyrics)")
        else:
            lrc_text = lrc_path.read_text(encoding="utf-8")

    cho = build_chordpro(changes, lrc_text, args.title, args.artist)

    if args.output:
        Path(args.output).write_text(cho, encoding="utf-8")
        log(f"wrote {args.output}")
        log("Next: review + correct, then validate with scripts/validate-cho.sh")
    else:
        sys.stdout.write(cho)
    return 0


if __name__ == "__main__":
    sys.exit(main())
