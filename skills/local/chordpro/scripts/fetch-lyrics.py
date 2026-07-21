#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27,<1",
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
            rec: dict | None = None
            resp = client.get(f"{LRCLIB}/get", params=get_params)
            if resp.status_code == 200:
                rec = resp.json()
                log(f"exact match: {rec.get('artistName')} – {rec.get('trackName')}")
            elif resp.status_code == 404:
                log("exact /get miss; trying /search…")
                sresp = client.get(
                    f"{LRCLIB}/search",
                    params={"artist_name": args.artist, "track_name": args.track},
                )
                sresp.raise_for_status()
                results = sresp.json() or []
                if not results:
                    log("no results from LRCLIB search")
                    return 3
                if args.duration:
                    results.sort(
                        key=lambda r: abs((r.get("duration") or 0) - args.duration)
                    )
                rec = results[0]
                log(
                    f"best search match: {rec.get('artistName')} – "
                    f"{rec.get('trackName')} ({rec.get('duration')}s)"
                )
            else:
                resp.raise_for_status()
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
