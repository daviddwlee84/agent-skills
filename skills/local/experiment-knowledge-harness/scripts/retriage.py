#!/usr/bin/env python3
"""List ROADMAP items whose depends-on findings are overturned/weakened.

Priorities are functions of findings; when a finding flips, the priorities
computed from it are stale. Run this after every overturn, and periodically.

Usage:
  retriage.py [--root DIR] [--all]

  --all   also show items whose dependencies are healthy (full dependency audit)

Exit code 1 when any item needs re-triage (CI-able).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import CONCLUDED_STATUSES, iter_experiments, parse_ledger, parse_roadmap, resolve_root  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="experiments root (default: auto-detect)")
    ap.add_argument("--all", action="store_true", help="show healthy dependencies too")
    args = ap.parse_args()

    root = resolve_root(args.root)
    ledger = parse_ledger(root / "LEDGER.md")
    items = parse_roadmap(root / "ROADMAP.md")
    exps = {f"#{e.id}": e for e in iter_experiments(root)}

    stale: list[tuple[str, str, str]] = []  # (lane, title, reason)
    healthy: list[tuple[str, str, str]] = []

    for it in items:
        if not it.depends_on:
            continue
        for dep in it.depends_on:
            if dep.startswith("F-"):
                f = ledger.findings.get(dep)
                if f is None:
                    stale.append((it.lane, it.title, f"{dep} missing from LEDGER"))
                elif f.status == "overturned":
                    stale.append((it.lane, it.title, f"{dep} OVERTURNED by {f.overturned_by}"))
                elif f.status == "weakened":
                    stale.append((it.lane, it.title, f"{dep} weakened by {f.weakened_by}"))
                else:
                    healthy.append((it.lane, it.title, f"{dep} active"))
            else:  # "#NNN" — experiment must be concluded
                e = exps.get(dep)
                if e is None:
                    stale.append((it.lane, it.title, f"{dep} matches no experiment"))
                else:
                    status = str(e.meta.get("status", ""))
                    if status in CONCLUDED_STATUSES:
                        healthy.append((it.lane, it.title, f"{dep} {status}"))
                    else:
                        healthy.append((it.lane, it.title, f"{dep} still {status or 'unknown'} (blocking)"))

    if stale:
        print(f"RE-TRIAGE NEEDED — {len(stale)} item(s) rest on moved ground:\n")
        for lane, title, reason in stale:
            print(f"  [{lane[3:]}] {title}\n      ↳ {reason}")
        print("\nRe-sort these with the user (priority was computed from the old belief).")
    else:
        print("all depends-on references are healthy — no re-triage needed")

    if args.all and healthy:
        print(f"\nhealthy/blocking dependencies ({len(healthy)}):")
        for lane, title, reason in healthy:
            print(f"  [{lane[3:]}] {title}  ({reason})")

    sys.exit(1 if stale else 0)


if __name__ == "__main__":
    main()
