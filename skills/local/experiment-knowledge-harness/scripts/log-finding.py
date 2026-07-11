#!/usr/bin/env python3
"""Append a finding to LEDGER.md (and optionally overturn an existing one).

Usage:
  log-finding.py --statement "Under half-spread costs, IS argmax has no OOS edge" \
      --evidence "#001" [--link "001-threshold-search/REPORT.md"] \
      [--overturns F-004] [--weakens F-006] [--date 2026-07-06] [--root DIR]

Behaviour:
  - Allocates the next F-NNN id.
  - Inserts the new finding at the END of ## Active (chronological order).
  - --overturns F-xxx: moves that finding to ## Overturned with
    strikethrough + `overturned <date> by F-new` annotation.
  - --weakens F-xxx: appends `(weakened by F-new)` to that active finding.
  - Re-validates the ledger afterwards; prints a retriage reminder when any
    ROADMAP item depends on the touched findings.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import ACTIVE_RE, parse_ledger, parse_roadmap, report_problems, resolve_root  # noqa: E402


def find_active_line(lines: list[str], fid: str) -> int:
    for i, ln in enumerate(lines):
        m = ACTIVE_RE.match(ln)
        if m and m.group(1) == fid:
            return i
    sys.exit(f"error: {fid} not found as a single-line active finding (multi-line items: edit by hand)")


def item_extent(lines: list[str], start: int) -> int:
    """End index (exclusive) of the item starting at `start` (continuation lines)."""
    j = start + 1
    while j < len(lines) and lines[j].strip() and (lines[j].startswith(("  ", "\t"))):
        j += 1
    return j


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--statement", required=True, help="the finding text (quantified, decision-relevant)")
    ap.add_argument("--evidence", required=True, help='"#NNN" experiment ref, or "ext"')
    ap.add_argument("--link", default="", help="optional relative evidence link target")
    ap.add_argument("--overturns", default=None, help="F-NNN to move to the Overturned lane")
    ap.add_argument("--weakens", default=None, help="F-NNN to mark as weakened by the new finding")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--root", help="experiments root (default: auto-detect)")
    args = ap.parse_args()

    if not re.fullmatch(r"#\d{3,}|ext", args.evidence):
        sys.exit('error: --evidence must be "#NNN" or "ext"')

    root = resolve_root(args.root)
    ledger_path = root / "LEDGER.md"
    ledger = parse_ledger(ledger_path)
    next_num = max((int(f[2:]) for f in ledger.findings), default=0) + 1
    new_fid = f"F-{next_num:03d}"

    lines = ledger_path.read_text(encoding="utf-8").splitlines()

    statement = args.statement.rstrip(".") + "."
    new_line = f"- **{new_fid}** [{args.date}] ({args.evidence}) {statement}"
    if args.link:
        new_line += f" → [evidence]({args.link})"

    # locate lane boundaries
    active_start = overturned_start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## Active":
            active_start = i
        elif ln.strip() == "## Overturned":
            overturned_start = i
    if active_start is None or overturned_start is None or overturned_start < active_start:
        sys.exit("error: LEDGER.md must have ## Active followed by ## Overturned")

    # insert new finding at end of Active lane (before trailing blank lines)
    insert_at = overturned_start
    while insert_at - 1 > active_start and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines[insert_at:insert_at] = [new_line]

    if args.weakens:
        idx = find_active_line(lines, args.weakens)
        lines[idx] = lines[idx].rstrip() + f" (weakened by {new_fid})"

    if args.overturns:
        idx = find_active_line(lines, args.overturns)
        end = item_extent(lines, idx)
        item = " ".join([lines[idx]] + [ln.strip() for ln in lines[idx + 1 : end]])
        m = ACTIVE_RE.match(item)
        assert m, "validated above"
        fid, date, source, text = m.groups()
        moved = f"- ~~**{fid}**~~ [{date}] ({source}) {text} — overturned {args.date} by {new_fid}"
        del lines[idx:end]
        lines.append(moved)

    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"logged: {new_fid} → {ledger_path}")

    problems: list[str] = []
    parse_ledger(ledger_path, problems)
    rc = report_problems(problems)

    touched = {new_fid} | {f for f in (args.overturns, args.weakens) if f}
    items = parse_roadmap(root / "ROADMAP.md")
    hit = [it for it in items if set(it.depends_on) & touched]
    if hit:
        print(f"\nNOTE: {len(hit)} ROADMAP item(s) depend on touched findings — run retriage.py:")
        for it in hit:
            print(f"  - [{it.lane[3:]}] {it.title}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
