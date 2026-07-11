#!/usr/bin/env python3
"""Allocate the next experiment id and scaffold <NNN>-<slug>/REPORT.md.

Usage:
  new-experiment.py --title "Slippage calibration vs ATP fills" \
      --question "Is half-spread taker cost the right execution model?" \
      --axis "slippage model" --baseline "#001 half_spread-v2" \
      [--spec half_spread-v2] [--slug slippage-calibration] \
      [--tags execution,costs] [--status planned] [--root DIR]

Prints the created REPORT path. Fill in the Pre-registration section
BEFORE running anything (hypothesis / success criteria / decision rule).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import iter_experiments, resolve_root  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "report.md.template"


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:48]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", required=True)
    ap.add_argument("--question", required=True, help="the research question this answers")
    ap.add_argument("--axis", required=True, help="THE one ablation axis")
    ap.add_argument("--baseline", required=True, help='named baseline, e.g. "#001 half_spread-v2"')
    ap.add_argument("--spec", default="v1", help="comparability spec label (default: v1)")
    ap.add_argument("--slug", default=None, help="folder slug (default: derived from title)")
    ap.add_argument("--tags", default="", help="comma-separated tags")
    ap.add_argument("--status", default="planned", choices=["planned", "running"])
    ap.add_argument("--root", help="experiments root (default: auto-detect)")
    args = ap.parse_args()

    root = resolve_root(args.root)
    exps = iter_experiments(root)
    next_id = max((int(e.id) for e in exps if e.id.isdigit()), default=0) + 1
    nnn = f"{next_id:03d}"
    slug = args.slug or slugify(args.title)
    folder = root / f"{nnn}-{slug}"
    if folder.exists():
        sys.exit(f"error: {folder} already exists")

    today = dt.date.today().isoformat()
    tags = ", ".join(t.strip() for t in args.tags.split(",") if t.strip())
    text = TEMPLATE.read_text(encoding="utf-8")
    for src, dst in (
        ("<NNN>", nnn),
        ("<slug>", slug),
        ("<TITLE>", args.title),
        ("<RESEARCH QUESTION>", args.question),
        ("<THE ONE ABLATION AXIS>", args.axis),
        ("<#NNN ref or explicit config>", args.baseline),
        ("<COMPARABILITY SPEC LABEL>", args.spec),
        ("<YYYY-MM-DD>", today),
        ("status: planned", f"status: {args.status}"),
        ("tags: []", f"tags: [{tags}]" if tags else "tags: []"),
    ):
        text = text.replace(src, dst)

    folder.mkdir(parents=True)
    report = folder / "REPORT.md"
    report.write_text(text, encoding="utf-8")
    print(f"created: {report}")
    print("next: write the Pre-registration section BEFORE running anything,")
    print("      then add/refresh the ROADMAP entry and run render-index.py")


if __name__ == "__main__":
    main()
