#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27,<1",
#   "pypinyin>=0.51",
# ]
# ///
"""fetch-lyrics.py — Fetch lyrics from LRCLIB (free, no API key).

LRCLIB is the default lyrics source for this skill: open, key-less,
cross-platform, and it returns time-synced .lrc when available. Lyrics (the
data) go to stdout or --output; diagnostics go to stderr.

Run with uv (self-contained via PEP 723 inline metadata):

    uv run fetch-lyrics.py --artist "Adele" --track "Hello" --duration 295
    uv run fetch-lyrics.py --plain --artist "..." --track "..." -o out.txt

Other sources (Musixmatch, NetEase, QQ, Genius, Mojim) are documented in
references/lyrics-sources.md — this script intentionally ships only the open
LRCLIB path and does not scrape.

Exit codes:
  0  lyrics found and emitted
  1  invalid arguments
  3  no matching lyrics found
  4  network / API error
"""
from __future__ import annotations

import argparse
import sys

import httpx

LRCLIB = "https://lrclib.net/api"
UA = "chordpro-skill/1.0 (agent-skills; +https://github.com/daviddwlee84/agent-skills)"


def log(msg: str) -> None:
    """Diagnostics -> stderr."""
    print(msg, file=sys.stderr)


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fetch-lyrics.py",
        description="Fetch lyrics from LRCLIB (synced .lrc by default, --plain for text).",
        epilog=(
            "Examples:\n"
            '  uv run fetch-lyrics.py --artist "Adele" --track "Hello" --duration 295\n'
            '  uv run fetch-lyrics.py --plain --artist "周杰倫" --track "晴天"\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--artist", required=True, help="Artist / performer name.")
    p.add_argument("--track", required=True, help="Track / song title.")
    p.add_argument("--album", help="Album name (improves exact-match on /get).")
    p.add_argument(
        "--duration",
        type=int,
        help="Track duration in seconds (helps disambiguate on /get and /search).",
    )
    p.add_argument(
        "--plain",
        action="store_true",
        help="Return plain text instead of the synced .lrc.",
    )
    p.add_argument("-o", "--output", help="Write lyrics to this file instead of stdout.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the requests that would be made, then exit.",
    )
    return p


def _emit(text: str, output: str | None) -> None:
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(text.rstrip("\n") + "\n")
        log(f"wrote {output} ({len(text.splitlines())} lines)")
    else:
        sys.stdout.write(text.rstrip("\n") + "\n")


def _has_cjk(s: str) -> bool:
    return any(
        0x4E00 <= ord(c) <= 0x9FFF
        or 0x3040 <= ord(c) <= 0x30FF
        or 0xAC00 <= ord(c) <= 0xD7AF
        for c in s
    )


def _romanize_variants(s: str) -> list[str]:
    """Romanization candidates for CJK text. LRCLIB indexes names the conventional
    way (surname + concatenated given name, e.g. 李榮浩 -> 'Li Ronghao'), so try that
    plus a per-syllable form ('Li Rong Hao')."""
    try:
        from pypinyin import lazy_pinyin
    except ImportError:
        return [s]
    sylls = [w for w in lazy_pinyin(s) if w]
    if not sylls:
        return [s]
    per_syllable = " ".join(w.capitalize() for w in sylls)  # Li Rong Hao / Li Bai
    name = sylls[0].capitalize()
    if len(sylls) > 1:
        name += " " + "".join(sylls[1:]).capitalize()  # Li Ronghao / Li Bai
    out: list[str] = []
    for v in (name, per_syllable):
        if v and v not in out:
            out.append(v)
    return out


def _lookup(client, artist, track, album, duration):
    """Try LRCLIB /get then /search; return the best record or None."""
    params: dict[str, object] = {"artist_name": artist, "track_name": track}
    if album:
        params["album_name"] = album
    if duration:
        params["duration"] = duration
    resp = client.get(f"{LRCLIB}/get", params=params)
    if resp.status_code == 200:
        rec = resp.json()
        log(f"exact match: {rec.get('artistName')} – {rec.get('trackName')}")
        return rec
    if resp.status_code != 404:
        resp.raise_for_status()
    log("exact /get miss; trying /search…")
    sresp = client.get(
        f"{LRCLIB}/search", params={"artist_name": artist, "track_name": track}
    )
    sresp.raise_for_status()
    results = sresp.json() or []
    if not results:
        return None
    if duration:
        results.sort(key=lambda r: abs((r.get("duration") or 0) - duration))
    rec = results[0]
    log(
        f"best search match: {rec.get('artistName')} – "
        f"{rec.get('trackName')} ({rec.get('duration')}s)"
    )
    return rec


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)

    get_params: dict[str, object] = {
        "artist_name": args.artist,
        "track_name": args.track,
    }
    if args.album:
        get_params["album_name"] = args.album
    if args.duration:
        get_params["duration"] = args.duration

    if args.dry_run:
        log(f"[dry-run] GET {LRCLIB}/get params={get_params}")
        log(
            f"[dry-run] fallback GET {LRCLIB}/search "
            f"params={{'artist_name': {args.artist!r}, 'track_name': {args.track!r}}}"
        )
        return 0

    try:
        with httpx.Client(headers={"User-Agent": UA}, timeout=20.0) as client:
            rec = _lookup(client, args.artist, args.track, args.album, args.duration)
            if rec is None and (_has_cjk(args.artist) or _has_cjk(args.track)):
                for a in _romanize_variants(args.artist):
                    for t in _romanize_variants(args.track):
                        if (a, t) == (args.artist, args.track):
                            continue
                        log(f"CJK miss; retrying romanized: {a!r} / {t!r}")
                        rec = _lookup(client, a, t, args.album, args.duration)
                        if rec is not None:
                            break
                    if rec is not None:
                        break
    except httpx.HTTPError as exc:
        log(f"LRCLIB request failed: {exc}")
        return 4

    if rec is None:
        log("no matching lyrics found")
        return 3
    if rec.get("instrumental"):
        log("LRCLIB marks this track as instrumental — no lyrics available.")
        return 3

    synced = rec.get("syncedLyrics")
    plain = rec.get("plainLyrics")

    if args.plain:
        text = plain or ""
        if not text:
            log("no plain lyrics available for this track")
            return 3
    else:
        text = synced or ""
        if not text:
            log("no synced .lrc available; falling back to plain text (--plain)")
            text = plain or ""
        if not text:
            log("no lyrics (synced or plain) available for this track")
            return 3

    _emit(text, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
