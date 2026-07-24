#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27,<1",
# ]
# ///
"""chart-to-cho.py — Convert an existing online chord chart into aligned ChordPro.

Fetches a human-made chart from **Chord4** (chord4.com / 和弦网 — primary, best for
Mandarin) or **Ultimate Guitar** (fallback) and converts it to inline ChordPro,
**preserving the chart's own chord-to-syllable alignment** rather than re-aligning
by eye. That faithful-transcription property is the whole point: the source already
encodes which syllable each chord sits on — Chord4 via parenthesized-syllable
markup (`後來的生(活)` → the chord above sits on 活), Ultimate Guitar via monospace
columns — so we reproduce it exactly instead of guessing. Re-merging fetched chords
onto separately-fetched lyrics is what drops alignment; this script doesn't do that.

The chart body (data) goes to stdout or --output; diagnostics go to stderr.

Chord4 access note: bare requests are Cloudflare-blocked, so this sends a browser
User-Agent + Accept-Language and accepts gzip. Simplified vs traditional is a URL
variant on the same tab id (`/zh-hant/tabs/N` = traditional, `/tabs/N` = simplified).

Examples:
    uv run chart-to-cho.py --url https://chord4.com/zh-hant/tabs/30689 -o song.cho
    uv run chart-to-cho.py --site ug --url https://tabs.ultimate-guitar.com/tab/oasis/wonderwall-chords-27596
    uv run chart-to-cho.py --html saved.html --site chord4        # parse a saved page
    curl -sL ... | uv run chart-to-cho.py --html - --site chord4  # or from stdin

Exit codes:
  0  chart parsed and emitted
  1  invalid arguments
  3  could not find/parse the chart in the page
  4  network / fetch error
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata

# --- shared helpers ---------------------------------------------------------

# CJK unified ideographs (+ ext-A + compatibility) — enough to tell a lyric line
# (has Han characters) from a chord line (Latin chord tokens only).
CJK = re.compile(r"[㐀-鿿豈-﫿]")
# A chord token starts with a root A–G, optional accidental, quality/extension,
# and an optional /bass. Deliberately permissive on the tail (maj7, add9, sus4…).
CHORD_TOKEN = re.compile(r"^[A-G][#b]?[A-Za-z0-9()+\-]*(?:/[A-G][#b]?)?$")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def has_cjk(s: str) -> bool:
    return bool(CJK.search(s))


def read_source(url: str | None, html_path: str | None, site: str) -> str:
    """Return raw HTML from --html (file or '-' for stdin) or by fetching --url."""
    if html_path:
        if html_path == "-":
            return sys.stdin.read()
        with open(html_path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    # network path — import httpx lazily so --html / --help work without it
    import httpx

    lang = "zh-TW,zh;q=0.9,en;q=0.8" if site != "ug" else "en-US,en;q=0.9"
    # NB: advertise only gzip/deflate — httpx doesn't decode brotli without the extra
    # 'brotli' package, and Chord4 will send 'br' if offered, yielding garbled bytes.
    headers = {"User-Agent": UA, "Accept-Language": lang, "Accept-Encoding": "gzip, deflate"}
    with httpx.Client(headers=headers, timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


# --- Chord4 -----------------------------------------------------------------


def chord4_pre(raw: str) -> str:
    """Extract the single chords-over-lyrics <pre> from Chord4's tabs_content div."""
    m = re.search(r'<div class="tabs_content">\s*<pre>(.*?)</pre>', raw, re.S)
    if not m:
        m = re.search(r"<pre>(.*?)</pre>", raw, re.S)
    if not m:
        raise ValueError("no <pre> chart block found (is this a Chord4 tab page?)")
    return html.unescape(m.group(1))


def chord4_meta(raw: str, header_text: str) -> dict:
    """Pull title/artist (og:title) + written key/capo/credits (pre header)."""
    meta: dict = {}
    m = re.search(r'<meta property="og:title" content="([^"]+)"', raw)
    if m:
        parts = [p.strip() for p in m.group(1).split(" - ")]
        # "說好不哭 - 周杰倫 - 吉他譜 - Chord4"
        if parts:
            meta["title"] = parts[0]
        if len(parts) >= 2:
            meta["artist"] = parts[1]
    # Key / Play / Capo — tolerate `Key=Bb`, `Key:=Em`, `Key: G`, on one line or
    # separate lines. When a distinct Play= exists, Key= is the SOUNDING key and
    # Play= is what you finger (→ {key}); otherwise Key= is the fingering key.
    def _find(pat: str):
        mm = re.search(pat, header_text, re.I)
        return mm.group(1) if mm else None

    key = _find(r"Key\s*[:=]+\s*([A-G][#b]?m?)")
    play = _find(r"Play\s*[:=]+\s*([A-G][#b]?m?)")
    capo = _find(r"Capo\s*[:=]+\s*(\d+)")
    if play:
        meta["sound_key"] = key
        meta["key"] = play
    elif key:
        meta["key"] = key
    if capo and capo != "0":
        meta["capo"] = capo
    for line in header_text.splitlines():
        if line.startswith("詞"):
            meta["lyricist"] = _after_colon(line)
        elif line.startswith("曲"):
            meta["composer"] = _after_colon(line)
        elif line.startswith("編配") or "編配者" in line:
            meta["arranger"] = re.split(r"[:：]", line, maxsplit=1)[-1].strip()
    return meta


def _after_colon(line: str) -> str:
    # "詞: 方文山 Lyrics/ Vincent Fang" → "方文山" (drop the English gloss)
    val = re.split(r"[:：]", line, maxsplit=1)[-1].strip()
    val = re.split(r"\s+(?:Lyrics?|Song|Music)\b", val)[0].strip()
    return val


_HDR_CJK = re.compile(
    r"^(詞|曲|作詞|作曲|編配|編曲|填詞|演唱|監製|原唱|製作|和聲|吉他|節奏|速度)[\w者]{0,3}\s*[:：]"
)
_HDR_EN = re.compile(
    r"^(Key|Play|Capo|Tuning|Tune|Arranged|Arr|Lyrics?|Music|Composed|Composer|"
    r"Artist|By|Song|BPM|Tempo)\b",
    re.I,
)
_HDR_SEP = re.compile(r"^[-=_—]{3,}$")
_FINGERING = re.compile(r"^\S+\s+[x0-9X]{4,7}$")


def chord4_split_header(lines: list[str]) -> int:
    """Index where the chart body begins.

    Skip the header line-by-line — credits (CJK `詞：/編配者：`, ASCII `Arranged`,
    `Key=/Play=/Capo=`), the `----` separator, and the `Name  frets` fingering
    table — and stop at the first real content line. Anchoring on line *content*
    (not on `[section]`/`|`) means charts that use plain `Intro:`-style text labels
    with no pipes still get their header stripped, so the `Key=` line lands in the
    header where the metadata parser can see it. (CJK credit words are colon-anchored
    because regex `\\b` word boundaries don't fire between two Han characters.)
    """
    for idx, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if _HDR_CJK.match(s) or _HDR_EN.match(s) or _HDR_SEP.match(s) or _FINGERING.match(s):
            continue
        return idx
    return 0


def is_chord_line(line: str) -> bool:
    toks = [t for t in line.replace("|", " ").split() if t != "*"]
    if not toks:
        return "|" in line
    chordish = sum(1 for t in toks if CHORD_TOKEN.match(t))
    return chordish >= max(1, (len(toks) + 1) // 2)


def chord_tokens(line: str) -> list[str]:
    # bars/repeat-stars may be glued to a chord (|Gm, C7|, |G|) — detach them first
    toks = []
    for raw in line.split():
        for p in re.findall(r"[^|*]+", raw):
            if CHORD_TOKEN.match(p):
                toks.append(p)
    return toks


def instrumental_line(line: str) -> str:
    """A chord line with no sung syllables → inline chords, keeping | bar markers.

    A bar can be glued to a chord in the source (`|Gm`, `C7|`); split those so the
    chord isn't lost, while keeping the bar as a visual separator.
    """
    out = []
    for raw in line.split():
        for p in re.findall(r"\||[^|]+", raw):
            if p == "|":
                out.append("|")
            elif CHORD_TOKEN.match(p):
                out.append(f"[{p}]")
        # stray '*' repeat markers fall through (not a bar, not a chord)
    return " ".join(out)


def pair_chord_lyric(chords: list[str], lyric: str) -> str:
    """Replace the Nth (marker) in the lyric with [chordN], preserving alignment.

    Chord4 binds ordinally: the Nth chord token pairs with the Nth `(…)` marker.
    An empty `( )` marker → a chord with no syllable (lead-in or instrumental beat)
    → a bare [chord] at that spot. Faithful to the source, including held beats.
    """
    lyric = re.sub(r"^\s*\*\s*", "", lyric)  # strip repeat-open marker
    lyric = re.sub(r"\s*\*\s*$", "", lyric)  # strip repeat-close marker
    it = iter(chords)

    def repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        ch = next(it, None)
        return inner if ch is None else f"[{ch}]{inner}"

    out = re.sub(r"\(([^)]*)\)", repl, lyric)
    leftover = list(it)
    if leftover:  # fewer markers than chords — append the rest so none are lost
        out = out.rstrip() + " " + " ".join(f"[{c}]" for c in leftover)
    out = re.sub(r" {2,}", " ", out).strip()
    return out


def _display_width(ch: str) -> int:
    """Terminal cells a char occupies — CJK/fullwidth = 2, so column math lines up."""
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def col_map_cjk(chord_line: str, lyric: str) -> str:
    """Chords-above-lyrics layout: map each chord's column onto the syllable beneath.

    The other Chord4 layout puts a chord line directly above the lyric, aligned in a
    monospace grid where CJK glyphs take 2 cells. Insert [chord] before the syllable
    whose display-column span contains the chord's column. This is the CJK-width math
    a2crd gets wrong — done right here.
    """
    lyric = re.sub(r"\s*\*\s*$", "", lyric.rstrip("\n"))
    chord_line = chord_line.replace("|", " ")  # detach glued bars (|Gm, C7|); keeps columns
    # display-column where each lyric char starts
    starts, col = [], 0
    for ch in lyric:
        starts.append(col)
        col += _display_width(ch)
    total = col
    inserts = []
    for m in re.finditer(r"\S+", chord_line):
        tok = m.group(0)
        if tok in ("|", "*") or not CHORD_TOKEN.match(tok):
            continue
        ccol = m.start()  # chord line is ASCII → index == display column
        if ccol >= total:
            idx = len(lyric)
        else:
            idx = 0
            for k, st in enumerate(starts):
                if st <= ccol:
                    idx = k
                else:
                    break
        inserts.append((idx, tok))
    res = lyric
    for idx, chord in sorted(inserts, key=lambda x: x[0], reverse=True):
        c = min(idx, len(res))
        res = res[:c] + f"[{chord}]" + res[c:]
    return re.sub(r" {2,}", " ", res).strip()


def parse_chord4(raw: str) -> tuple[list[str], dict]:
    pre = chord4_pre(raw)
    lines = pre.split("\n")
    body_start = chord4_split_header(lines)
    meta = chord4_meta(raw, "\n".join(lines[:body_start]))

    body = lines[body_start:]
    out: list[str] = []
    i, n = 0, len(body)
    while i < n:
        line = body[i].rstrip()
        s = line.strip()
        if not s:
            out.append("")
            i += 1
            continue
        if "<" in line and ">" in line:  # strip embedded HTML (charts sometimes <img> a tab pic)
            without = re.sub(r"<[^>]+>", "", line)
            if not without.strip():
                out.append("{comment: (chart image in source omitted — see the URL)}")
                i += 1
                continue
            line, s = without, without.strip()
        m = re.match(r"^\[([^\]]+)\]$", s)
        if m:  # section label
            out.append(f"{{comment: {m.group(1)}}}")
            i += 1
            continue
        if re.match(r"^Repeat\b", s, re.I):
            out.append("{comment: (repeat the section marked *)}")
            i += 1
            continue
        # 'Intro:' / '副歌:' / 'RAP:' text label, optionally with inline chords after it.
        # Only treat as a label when what follows the colon is empty or pure chords —
        # so a lyric like "他說：..." or "Well: I don't know" is left alone.
        lm = re.match(r"^\s*([A-Za-z][\w /-]{0,14}|[一-鿿]{1,6})\s*[:：]\s*(.*)$", line)
        if lm:
            label, rest = lm.group(1).strip(), lm.group(2).strip()
            rest_toks = rest.split()
            if not has_cjk(rest) and (not rest_toks or all(t == "|" or CHORD_TOKEN.match(t) for t in rest_toks)):
                out.append(f"{{comment: {label}}}")
                if rest_toks:
                    out.append(instrumental_line(rest))
                i += 1
                continue
        if not has_cjk(line) and is_chord_line(line):
            chords = chord_tokens(line)
            nxt = body[i + 1] if i + 1 < n else ""
            if nxt.strip() and (has_cjk(nxt) or "(" in nxt):
                if has_cjk(nxt):
                    # two Chord4 layouts: parenthesized-syllable markers → ordinal
                    # pairing; plain chords-above-lyrics → CJK-aware column mapping.
                    if "(" in nxt:
                        out.append(pair_chord_lyric(chords, nxt))
                    else:
                        out.append(col_map_cjk(line, nxt))
                else:  # marker-only / no-CJK lyric line → instrumental
                    out.append(instrumental_line(line))
                i += 2
                continue
            out.append(instrumental_line(line))  # no lyric follows
            i += 1
            continue
        # a lyric/text line with no preceding chord line (continuation) — keep plain
        out.append(re.sub(r"[()*]", "", line).rstrip())
        i += 1
    return _trim_blanks(out), meta


# --- Ultimate Guitar --------------------------------------------------------


def parse_ug(raw: str) -> tuple[list[str], dict]:
    m = re.search(r'<div class="js-store" data-content="([^"]*)"', raw)
    if not m:
        raise ValueError("no js-store data-content found (is this a UG chords page?)")
    data = json.loads(html.unescape(m.group(1)))
    page = data["store"]["page"]["data"]
    content = page["tab_view"]["wiki_tab"]["content"]
    tab = page.get("tab", {})
    tv_meta = page["tab_view"].get("meta", {}) or {}
    meta = {
        "title": tab.get("song_name"),
        "artist": tab.get("artist_name"),
        "key": tab.get("tonality_name") or tv_meta.get("tonality"),
        "capo": tv_meta.get("capo"),
    }

    text = content.replace("\r\n", "\n").replace("[tab]", "").replace("[/tab]", "")
    lines = text.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            out.append("")
            i += 1
            continue
        if re.match(r"^\[[^\]]+\]$", s) and "[ch]" not in s:  # section header
            out.append(f"{{comment: {s[1:-1]}}}")
            i += 1
            continue
        if "[ch]" in line:  # chord line
            nxt = lines[i + 1] if i + 1 < n else ""
            if nxt.strip() and "[ch]" not in nxt and not re.match(r"^\[[^\]]+\]$", nxt.strip()):
                out.append(ug_map(line, nxt))
                i += 2
            else:  # instrumental — bare chords
                out.append(" ".join(f"[{c}]" for _, c in ug_positions(line)))
                i += 1
            continue
        out.append(re.sub(r"\[/?ch\]", "", line).rstrip())
        i += 1
    return _trim_blanks(out), meta


def ug_positions(chord_line: str) -> list[tuple[int, str]]:
    """Visual column → chord, by stripping [ch]…[/ch] and tracking real columns."""
    positions: list[tuple[int, str]] = []
    visual_len = 0
    idx = 0
    s = chord_line
    while idx < len(s):
        m = re.match(r"\[ch\](.*?)\[/ch\]", s[idx:])
        if m:
            positions.append((visual_len, m.group(1)))
            idx += m.end()
        else:
            visual_len += 1
            idx += 1
    return positions


def ug_map(chord_line: str, lyric: str) -> str:
    """Insert [chord] into the lyric at the chord's monospace column (ASCII-safe)."""
    lyric = lyric.rstrip("\n")
    for col, ch in sorted(ug_positions(chord_line), key=lambda x: x[0], reverse=True):
        c = min(col, len(lyric))
        lyric = lyric[:c] + f"[{ch}]" + lyric[c:]
    return lyric.rstrip()


# --- assembly ---------------------------------------------------------------


def _trim_blanks(lines: list[str]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        if ln == "" and (not out or out[-1] == ""):
            continue
        out.append(ln)
    while out and out[-1] == "":
        out.pop()
    return out


def build_cho(body: list[str], meta: dict, url: str | None, site: str) -> str:
    head: list[str] = []
    if meta.get("title"):
        head.append(f"{{title: {meta['title']}}}")
    if meta.get("artist"):
        head.append(f"{{artist: {meta['artist']}}}")
    if meta.get("composer"):
        head.append(f"{{composer: {meta['composer']}}}")
    if meta.get("lyricist"):
        head.append(f"{{lyricist: {meta['lyricist']}}}")
    if meta.get("key"):
        head.append(f"{{key: {meta['key']}}}")
    if meta.get("capo") not in (None, "", "0", 0):
        head.append(f"{{capo: {meta['capo']}}}")

    src = url or f"{site} chart"
    note = f"Source: {src}"
    if meta.get("arranger"):
        note += f" (arr. {meta['arranger']})"
    detail = []
    if meta.get("sound_key"):
        detail.append(f"sounds in {meta['sound_key']}")
    if meta.get("key"):
        detail.append(f"fingered in {meta['key']}")
    if meta.get("capo"):
        detail.append(f"capo {meta['capo']}")
    detail_s = "; ".join(detail)
    head.append(f"{{comment: {note}. {detail_s + '. ' if detail_s else ''}"
                "Published arrangement — verify against the recording (capo/key may differ). Personal use.}")
    return "\n".join(head) + "\n\n" + "\n".join(body) + "\n"


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chart-to-cho.py",
        description="Convert a Chord4 / Ultimate Guitar chart into aligned ChordPro.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Preserves the chart's own chord-to-syllable alignment (no re-merge).\n"
            "Chord4 = primary (Mandarin); Ultimate Guitar = fallback.\n\n"
            "Personal-use only: charts are user arrangements of copyrighted songs —\n"
            "keep the output local, don't redistribute, and cite the source (auto-added).\n"
        ),
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Chart URL (Chord4 tab page or UG chords page).")
    src.add_argument("--html", help="Read raw HTML from this file, or '-' for stdin.")
    p.add_argument(
        "--site",
        choices=("chord4", "ug", "auto"),
        default="auto",
        help="Which parser to use (default: auto-detect from URL/markup).",
    )
    p.add_argument("-o", "--output", help="Write ChordPro here instead of stdout.")
    p.add_argument(
        "--opencc",
        choices=("s2t", "t2s"),
        help="Convert Han characters simplified↔traditional (needs the 'opencc' "
        "package; try `uv run --with opencc chart-to-cho.py ...`). Chords/directives "
        "are unaffected. Tip: Chord4 also serves both via the URL (/zh-hant/tabs/N).",
    )
    p.add_argument("--dry-run", action="store_true", help="Print the plan, then exit.")
    return p


def opencc_convert(text: str, mode: str) -> str:
    """Simplified↔traditional on the Han characters only (chords/ASCII untouched)."""
    try:
        from opencc import OpenCC
    except ImportError:
        log("--opencc needs the 'opencc' package — skipping conversion. "
            "Re-run with: uv run --with opencc chart-to-cho.py …")
        return text
    return OpenCC(mode).convert(text)


def detect_site(url: str | None, raw: str | None) -> str:
    if url and "chord4.com" in url:
        return "chord4"
    if url and "ultimate-guitar.com" in url:
        return "ug"
    if raw and "js-store" in raw and "data-content" in raw:
        return "ug"
    return "chord4"


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    site = args.site

    if args.dry_run:
        resolved = site if site != "auto" else detect_site(args.url, None)
        log(f"[dry-run] source: {args.url or args.html}")
        log(f"[dry-run] parser: {resolved} (auto-detect may refine from markup)")
        log("[dry-run] would fetch (browser UA), parse chords-over-lyrics preserving")
        log("[dry-run] the chart's own alignment, and emit ChordPro to "
            f"{args.output or 'stdout'}.")
        return 0

    if site == "auto":
        site = detect_site(args.url, None)

    try:
        raw = read_source(args.url, args.html, site)
    except Exception as exc:  # noqa: BLE001 — surface any fetch/read failure cleanly
        log(f"could not read source: {exc}")
        return 4

    if args.site == "auto":  # refine now that we have markup
        site = detect_site(args.url, raw)

    try:
        body, meta = parse_ug(raw) if site == "ug" else parse_chord4(raw)
    except ValueError as exc:
        log(f"parse failed ({site}): {exc}")
        if site == "chord4" and "Attention Required" in raw:
            log("hint: Cloudflare challenge page — retry, or open the URL in a browser "
                "and save the HTML, then pass it with --html.")
        return 3

    if not any(l.strip() and not l.startswith("{") for l in body):
        log("parsed no chord/lyric lines — the page markup may have changed.")
        return 3

    cho = build_cho(body, meta, args.url, site)
    if args.opencc:
        cho = opencc_convert(cho, args.opencc)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(cho)
        log(f"wrote {args.output} ({site}; {sum(1 for l in body if l.strip())} chart lines)")
    else:
        sys.stdout.write(cho)
    log("NOTE: published arrangement — verify chords/capo/key against the recording. "
        "Run analyze-progression.py on the result to sanity-check the harmony.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
