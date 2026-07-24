#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""analyze-progression.py — Sanity-check a chord progression against music theory.

Detects the key, expresses every chord as a scale degree (Roman + Nashville),
labels each as diatonic / borrowed / secondary / out-of-key, and scores each
chord *move* against an empirical rock-corpus transition matrix. The point is to
catch a **mis-transcribed chord**: the strongest signal is a chord that is both
out-of-key AND reached by an improbable move. It also flags duplicate/floating
chords. This is a *sanity gate*, not an oracle — unusual ≠ wrong (see the footer).

Zero external dependencies (pure stdlib). `music21` is an OPTIONAL escalation for a
Krumhansl/Aarden key cross-check + richer secondary-dominant analysis; the core
runs without it.

Transition data: de Clercq & Temperley, "A Corpus Analysis of Rock Harmony,"
Popular Music 30(1):47–70 (2011), Tables 2–3. Rock Corpus (rockcorpus.midside.com),
CC BY 4.0. The corpus uses *root categories* (chord quality collapsed; applied
chords folded in), so transition scoring is by scale-degree ROOT relative to the
tonic — mode-independent, exactly as the data was built.

Examples:
    uv run analyze-progression.py song.cho
    uv run analyze-progression.py --key G --chords "G Em7 C D7 G"
    uv run analyze-progression.py --json song.cho

Report → stdout; diagnostics → stderr.

Exit codes:
  0  analysis emitted (0 also when it flags issues — flags are content, not errors)
  1  invalid arguments
  2  file not found
  3  no parseable chords found
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys

# --- embedded rock-corpus data (de Clercq & Temperley 2011) ------------------

# 12 root categories = semitone interval from tonic (0..11). Quality collapsed.
CATS = ["I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII"]

# Table 2 — marginal root distribution (share of all harmonies). SOURCED.
MARGINAL = {
    "I": 0.328, "bII": 0.005, "II": 0.036, "bIII": 0.026, "III": 0.019, "IV": 0.226,
    "#IV": 0.003, "V": 0.163, "bVI": 0.040, "VI": 0.072, "bVII": 0.081, "VII": 0.004,
}

# Table 3 — raw transition counts, rows = current, cols = next (CATS order). SOURCED.
_COUNTS = {
    "I":    [0, 25, 132, 94, 44, 1052, 2, 710, 104, 302, 470, 16],
    "bII":  [31, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 12],
    "II":   [120, 1, 0, 2, 20, 58, 0, 97, 0, 24, 10, 0],
    "bIII": [50, 6, 6, 0, 0, 64, 2, 2, 67, 0, 41, 0],
    "III":  [16, 0, 39, 0, 0, 46, 0, 6, 0, 60, 3, 4],
    "IV":   [1162, 14, 30, 98, 45, 0, 4, 514, 57, 72, 90, 4],
    "#IV":  [7, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0],
    "V":    [788, 0, 36, 6, 17, 392, 4, 0, 6, 191, 48, 0],
    "bVI":  [208, 0, 1, 20, 0, 22, 6, 22, 0, 10, 78, 0],
    "VI":   [144, 0, 87, 0, 32, 260, 0, 124, 21, 0, 3, 0],
    "bVII": [386, 0, 0, 11, 2, 188, 2, 26, 114, 6, 0, 0],
    "VII":  [18, 0, 0, 0, 12, 0, 4, 0, 0, 3, 0, 0],
}
_ALPHA = 3.0  # add-k smoothing so no transition is impossible (avoids log 0)
RARE_P = 0.03  # a move rarer than this is flagged "review"


def p_next(cur: str, nxt: str) -> float:
    """Smoothed P(next | current): (count + α·marginal) / (rowtotal + α)."""
    row = _COUNTS[cur]
    total = sum(row)
    return (row[CATS.index(nxt)] + _ALPHA * MARGINAL[nxt]) / (total + _ALPHA)


# --- chord-symbol parsing ----------------------------------------------------

LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
CHORD_RE = re.compile(r"^([A-G])([#b]*)(.*)$")


def parse_chord(sym: str):
    """'F#m7/C#' → (root_pc, triad_quality, bass_pc|None, ext, letter, acc, bass_name)."""
    m = CHORD_RE.match(sym)
    if not m:
        return None
    letter, acc, rest = m.group(1), m.group(2), m.group(3)
    root = (LETTER_PC[letter] + acc.count("#") - acc.count("b")) % 12
    bass = None
    bass_name = None
    if "/" in rest:
        rest, bass_sym = rest.split("/", 1)
        bass_name = bass_sym.strip()
        bm = CHORD_RE.match(bass_name)
        if bm:
            bass = (LETTER_PC[bm.group(1)] + bm.group(2).count("#") - bm.group(2).count("b")) % 12
    quality = classify_quality(rest)
    return root, quality, bass, rest, letter, acc, bass_name


def classify_quality(rest: str) -> str:
    r = rest
    if r.startswith("maj") or r.startswith("M") or r.startswith("Δ"):
        return "maj"
    if r.startswith(("dim", "°", "o")) or "m7b5" in r or r.startswith("ø") or "m7-5" in r:
        return "dim"
    if r.startswith("aug") or r.startswith("+"):
        return "aug"
    if r.startswith("sus"):
        return "sus"
    if r.startswith(("m", "min", "-")):
        return "min"
    return "maj"  # bare, 7, 6, 9, add9, etc.


# --- key scales + detection --------------------------------------------------

MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MAJOR_QUAL = ["maj", "min", "min", "maj", "maj", "min", "dim"]
NAT_MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]
NAT_MINOR_QUAL = ["min", "dim", "maj", "min", "min", "maj", "maj"]
# harmonic/melodic minor also make these diatonic (raised 6/7):
MINOR_EXTRA = {4: {"maj"}, 6: {"maj", "dim"}, 11: {"maj", "dim"}, 9: {"maj", "min"}}

MAJOR_KEY_SPELL = {0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F",
                   6: "F#", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"}
MINOR_KEY_SPELL = {0: "C", 1: "C#", 2: "D", 3: "Eb", 4: "E", 5: "F",
                   6: "F#", 7: "G", 8: "G#", 9: "A", 10: "Bb", 11: "B"}
LETTERS = "CDEFGAB"


def cof_pos(pc: int) -> int:
    return (pc * 7) % 12


def cof_dist(a: int, b: int) -> int:
    d = abs(cof_pos(a) - cof_pos(b))
    return min(d, 12 - d)


def diatonic_map(tonic: int, mode: str) -> dict:
    """pc → set of qualities that are diatonic at that pc in the key."""
    out: dict[int, set] = {}
    steps = MAJOR_STEPS if mode == "major" else NAT_MINOR_STEPS
    quals = MAJOR_QUAL if mode == "major" else NAT_MINOR_QUAL
    for st, q in zip(steps, quals):
        out.setdefault((tonic + st) % 12, set()).add(q)
    if mode == "minor":
        for st, qs in MINOR_EXTRA.items():
            out.setdefault((tonic + st) % 12, set()).update(qs)
    return out


def score_key(chords, tonic: int, mode: str) -> float:
    dia = diatonic_map(tonic, mode)
    score = 0.0
    for i, ch in enumerate(chords):
        root, qual = ch[0], ch[1]
        if root in dia:
            score += 3.0 if (qual in dia[root] or qual in ("sus", "aug")) else 1.2
        else:
            score -= 1.0 + 0.5 * cof_dist(root, tonic)
    # tonic-emphasis cues break the relative major/minor tie (shared scale)
    roots = [c[0] for c in chords]
    if roots:
        if roots[-1] == tonic:
            score += 3.0
        if roots[0] == tonic:
            score += 2.0
    # cadence bonus: V(→I) for major, V or bVII (→i) for minor
    for a, b in zip(chords, chords[1:]):
        if b[0] == tonic:
            iv = (a[0] - tonic) % 12
            if iv == 7 and a[1] == "maj":
                score += 1.5
            if mode == "minor" and iv == 10:
                score += 1.0
    return score


def detect_key(chords):
    cand = []
    for tonic in range(12):
        for mode in ("major", "minor"):
            cand.append((score_key(chords, tonic, mode), tonic, mode))
    cand.sort(reverse=True)
    return cand


# --- degree spelling (Roman + Nashville), letter-driven ----------------------

def key_letters(tonic: int, mode: str):
    spell = (MAJOR_KEY_SPELL if mode == "major" else MINOR_KEY_SPELL)[tonic]
    start = LETTERS.index(spell[0])
    letters = [LETTERS[(start + i) % 7] for i in range(7)]
    steps = MAJOR_STEPS if mode == "major" else NAT_MINOR_STEPS
    pcs = [(tonic + s) % 12 for s in steps]
    return letters, pcs


def _acc_str(offset: int) -> str:
    if offset == 0:
        return ""
    return ("#" if offset > 0 else "b") * abs(offset)


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]


def degree_labels(ch, tonic: int, mode: str):
    """Return (roman, nashville) for a chord in the key, letter-spelled."""
    root, qual, bass, rest, letter, acc, bass_name = ch
    letters, pcs = key_letters(tonic, mode)
    deg = letters.index(letter)  # 0..6, by letter name
    diat_pc = pcs[deg]
    offset = ((root - diat_pc + 6) % 12) - 6  # -.. small signed accidental
    accs = _acc_str(offset)
    base = ROMAN[deg]
    if qual in ("min", "dim"):
        rn = base.lower()
    else:
        rn = base
    deco = ""
    if qual == "dim":
        deco = "°"
    elif qual == "aug":
        deco = "+"
    elif qual == "sus":
        deco = "sus"
    ext = _ext_suffix(rest)
    roman = f"{accs}{rn}{deco}{ext}{_figbass(bass_name, bass, root)}"
    nash = f"{accs}{deg + 1}{'m' if qual == 'min' else ''}{'°' if qual == 'dim' else ''}"
    return roman, nash


def _ext_suffix(rest: str) -> str:
    if "maj7" in rest or "M7" in rest:
        return "maj7"
    for tag in ("7", "6", "9", "11", "13", "add9"):
        if tag in rest:
            return tag
    return ""


def _figbass(bass_name, bass, root) -> str:
    if bass is None or bass == root:
        return ""
    return "/" + (bass_name or str(bass))  # show the actual bass note


def root_category(root: int, tonic: int) -> str:
    return CATS[(root - tonic) % 12]


# --- diatonic-fit labeling ---------------------------------------------------

def fit_label(ch, tonic: int, mode: str) -> str:
    root, qual = ch[0], ch[1]
    dia = diatonic_map(tonic, mode)
    if root in dia and (qual in dia[root] or qual in ("sus",)):
        return "diatonic"
    # secondary dominant V/x: a maj/dom7 a fifth above a diatonic (non-tonic) degree.
    # Skip the tonic root itself — a major tonic in a minor key is Picardy/borrowed,
    # not V/iv.
    if qual == "maj" and root != tonic:
        target = (root + 5) % 12  # root is a fifth ABOVE target → target = root+5
        if target in dia and target != tonic:
            return f"secondary(V/{_deg_name(target, tonic, mode)})"
    # borrowed from parallel mode
    other = diatonic_map(tonic, "minor" if mode == "major" else "major")
    if root in other:
        return "borrowed"
    # common modal-mixture roots
    if (root - tonic) % 12 in (10, 8, 3):  # bVII, bVI, bIII
        return "borrowed"
    return "out-of-key"


def _deg_name(pc: int, tonic: int, mode: str) -> str:
    letters, pcs = key_letters(tonic, mode)
    if pc in pcs:
        i = pcs.index(pc)
        base = ROMAN[i]
        return base if (MAJOR_QUAL if mode == "major" else NAT_MINOR_QUAL)[i] == "maj" else base.lower()
    return root_category(pc, tonic)


# --- .cho / input extraction -------------------------------------------------

BRACKET = re.compile(r"\[([^\]]+)\]")


def chords_from_cho(text: str):
    """Extract (symbol, lineno, is_trailing, is_immediate_repeat) in order.

    is_immediate_repeat = the same chord occurs again with only whitespace/bars
    between (a redundant double), NOT merely a held chord with lyrics in between.
    """
    out = []
    for lineno, line in enumerate(text.splitlines()):
        s = line.strip()
        if s.startswith("#") or s.startswith("{"):
            continue
        toks = list(BRACKET.finditer(line))
        prev_sym, prev_end = None, None
        for m in toks:
            sym = m.group(1).strip()
            if sym.startswith("*") or not CHORD_RE.match(sym):
                continue
            # trailing = nothing but spaces / other chords after this bracket, on a
            # line that DOES contain lyric characters (a floating end-of-line chord)
            after = line[m.end():]
            has_lyric = bool(re.search(r"[^\s\[\]|/A-G#b0-9()majdinsu+°oØ.-]", line))
            trailing = has_lyric and not re.search(r"[^\s|]", re.sub(r"\[[^\]]*\]", "", after))
            dup = (has_lyric and sym == prev_sym and prev_end is not None
                   and not re.search(r"[^\s|]", line[prev_end:m.start()]))
            out.append((sym, lineno, trailing, dup))
            prev_sym, prev_end = sym, m.end()
    return out


# --- report ------------------------------------------------------------------

def parse_key_hint(s: str):
    """'G' → (7,'major'); 'Am' → (9,'minor'); 'F#m' → (6,'minor')."""
    m = re.match(r"^\s*([A-G])([#b]?)\s*(m|min|minor)?\s*$", s)
    if not m:
        return None
    pc = (LETTER_PC[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12
    return pc, ("minor" if m.group(3) else "major")


def analyze(chords_meta, key_hint=None):
    syms = [c[0] for c in chords_meta]
    parsed = [parse_chord(s) for s in syms]
    pairs = [(s, p) for s, p in zip(syms, parsed) if p]
    if not pairs:
        return None
    chords = [p for _, p in pairs]

    ranked = detect_key(chords)
    forced = parse_key_hint(key_hint) if key_hint else None
    if forced:
        tonic, mode = forced
        det_name = (MAJOR_KEY_SPELL if ranked[0][2] == "major" else MINOR_KEY_SPELL)[ranked[0][1]]
        det_name += f" {ranked[0][2]}"
        given_name = (MAJOR_KEY_SPELL if mode == "major" else MINOR_KEY_SPELL)[tonic] + f" {mode}"
        conf = "given"
        runner_name = det_name if det_name != given_name else "detection agrees"
    else:
        top_score, tonic, mode = ranked[0]
        runner = ranked[1]
        margin = top_score - runner[0]
        conf = "high" if margin >= 4 else "medium" if margin >= 1.5 else "low"
        runner_name = (MAJOR_KEY_SPELL if runner[2] == "major" else MINOR_KEY_SPELL)[runner[1]] + f" {runner[2]}"
    tonic_name = (MAJOR_KEY_SPELL if mode == "major" else MINOR_KEY_SPELL)[tonic]
    key_name = f"{tonic_name} {mode}"

    per_chord = []
    for (sym, _), ch in zip(pairs, chords):
        roman, nash = degree_labels(ch, tonic, mode)
        per_chord.append({
            "chord": sym, "roman": roman, "nashville": nash,
            "cat": root_category(ch[0], tonic), "fit": fit_label(ch, tonic, mode),
        })

    # transitions on the root-category sequence, collapsing adjacent repeats
    seq = [pc["cat"] for pc in per_chord]
    collapsed = [c for i, c in enumerate(seq) if i == 0 or c != seq[i - 1]]
    rare_agg: dict = {}
    logs = []
    for a, b in zip(collapsed, collapsed[1:]):
        p = p_next(a, b)
        logs.append(math.log(p))
        if p < RARE_P:
            e = rare_agg.setdefault((a, b), {"from": a, "to": b, "p": round(p, 3), "count": 0})
            e["count"] += 1
    trans = sorted(rare_agg.values(), key=lambda e: (-e["count"], e["p"]))

    # duplicate + floating warnings — aggregate by chord so a repeat-heavy chart
    # yields a one-line summary, not a wall of near-identical lines
    dup: dict = {}
    trail: dict = {}
    for sym, _lineno, trailing, is_dup in chords_meta:
        if is_dup:
            dup[sym] = dup.get(sym, 0) + 1
        if trailing:
            trail[sym] = trail.get(sym, 0) + 1
    warnings = []
    if dup:
        items = ", ".join(f"[{k}]×{v}" for k, v in sorted(dup.items(), key=lambda x: -x[1]))
        warnings.append(f"immediately repeated chords (redundant double, or a "
                        f"mis-transcription?): {items}")
    if trail:
        items = ", ".join(f"[{k}]×{v}" for k, v in sorted(trail.items(), key=lambda x: -x[1]))
        warnings.append(f"chords trailing past the last syllable of a line (instrumental "
                        f"beat, or a floater to fold into a bar?): {items}")

    # suspect = out-of-key AND reached by a rare move
    rare_targets = {t["to"] for t in trans}
    suspects = [pc["chord"] for pc in per_chord
                if pc["fit"] == "out-of-key" and pc["cat"] in rare_targets]

    n = len(per_chord)
    dia_ratio = sum(1 for c in per_chord if c["fit"] != "out-of-key") / n
    mean_lp = sum(logs) / len(logs) if logs else 0.0
    trans_score = max(0.0, min(1.0, (mean_lp - math.log(0.01)) / (math.log(0.35) - math.log(0.01))))
    plausibility = round(0.5 * dia_ratio + 0.5 * trans_score, 2)

    return {
        "key": key_name, "confidence": conf, "runner_up": runner_name,
        "chords": per_chord, "rare_transitions": trans, "suspects": suspects,
        "warnings": warnings, "plausibility": plausibility,
    }


def render(rep: dict) -> str:
    L = []
    if rep["confidence"] == "given":
        note = "" if rep["runner_up"] == "detection agrees" else f"  [detection suggests {rep['runner_up']}]"
        L.append(f"Key: {rep['key']}   [given]{note}")
    else:
        rel = f"  (or {rep['runner_up']}?)" if rep["confidence"] != "high" else ""
        L.append(f"Key: {rep['key']}   [confidence: {rep['confidence']}]{rel}")
    L.append("")
    L.append(f"{'Chord':<9}{'Roman':<9}{'Nash':<6}Fit")
    for c in rep["chords"]:
        L.append(f"{c['chord']:<9}{c['roman']:<9}{c['nashville']:<6}{c['fit']}")
    L.append("")
    if rep["rare_transitions"]:
        L.append("Transition check (rock-corpus prior) — surprising moves, review (not 'wrong'):")
        for t in rep["rare_transitions"]:
            times = f"  ×{t['count']}" if t["count"] > 1 else ""
            L.append(f"  {t['from']:>4} → {t['to']:<4}  rare (p≈{t['p']}){times}")
    else:
        L.append("Transition check: no improbable moves — progression is idiomatic.")
    if rep["suspects"]:
        L.append("")
        L.append("SUSPECT (out-of-key AND reached by a rare move) — likely mis-transcribed, double-check:")
        for s in rep["suspects"]:
            L.append(f"  {s}")
    if rep["warnings"]:
        L.append("")
        L.append("Warnings:")
        for w in rep["warnings"]:
            L.append(f"  {w}")
    L.append("")
    L.append(f"Progression plausibility: {rep['plausibility']}  "
             f"(0.5·diatonic-fit + 0.5·transition-likelihood)")
    L.append("")
    L.append("— Prior is rock-descriptive (de Clercq & Temperley 2011), not prescriptive: "
             "unusual ≠ wrong.")
    L.append("  Relative major/minor share a scale, so the key can be ambiguous; a wrong "
             "key cascades into wrong numerals.")
    return "\n".join(L)


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="analyze-progression.py",
        description="Key + Roman/Nashville degrees + rock-corpus transition sanity-check.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sanity gate for a fetched/authored chart — flags likely mis-transcribed chords.\n"
               "Data: de Clercq & Temperley 2011; Rock Corpus (CC BY 4.0).",
    )
    p.add_argument("file", nargs="?", help="A .cho file to analyze.")
    p.add_argument("--chords", help='Space-separated chords, e.g. "G Em7 C D7 G" (with --key).')
    p.add_argument("--key", help="Key hint, e.g. 'G' or 'Am' (optional; detection still runs).")
    p.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    return p


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    if args.chords:
        meta = [(s, 0, False, False) for s in args.chords.split()]
    elif args.file:
        import os
        if not os.path.isfile(args.file):
            log(f"file not found: {args.file}")
            return 2
        with open(args.file, encoding="utf-8") as fh:
            meta = chords_from_cho(fh.read())
    else:
        log("give a .cho file or --chords \"...\" (try --help)")
        return 1

    if not meta:
        log("no parseable chords found")
        return 3
    rep = analyze(meta, args.key)
    if rep is None:
        log("no parseable chords found")
        return 3
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json else render(rep))
    return 0


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
