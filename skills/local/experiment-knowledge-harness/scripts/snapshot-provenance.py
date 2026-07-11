#!/usr/bin/env python3
"""Emit a ready-to-paste `## Provenance` block for a REPORT.md.

Collects what can be collected mechanically (git SHA/dirty/branch, python &
package versions, hostname, timestamp) and templates the rest with
placeholders you must fill (data window, seeds, artifacts).

Usage:
  snapshot-provenance.py --cmd "uv run python scripts/run_meta_sweep.py --workers 8" \
      [--data "orders+snapshots 2026-05-13..2026-06-30 (34 d)"] \
      [--config-hash "grid cache schema v2"] [--spec "half_spread-v2 (fee 0.6bp, size 10)"] \
      [--seeds "deterministic"] [--artifacts "results/ (gitignored)"] \
      [--packages numpy,pandas,vectorbt] \
      [--mlflow "sqlite:///mlruns.db exp=threshold_search runs=..."] \
      [--repo DIR]

Pipe into the REPORT or use --append REPORT.md to write it directly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import socket
import subprocess
import sys
from pathlib import Path


def sh(args: list[str], cwd: Path) -> str:
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def pkg_versions(names: list[str]) -> str:
    from importlib import metadata

    out = []
    for name in names:
        try:
            out.append(f"{name} {metadata.version(name)}")
        except metadata.PackageNotFoundError:
            out.append(f"{name} <not installed>")
    return ", ".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", required=True, help="exact reproduction command(s); ';'-separate a chain")
    ap.add_argument("--data", default="<source + explicit date window + staging/filters>")
    ap.add_argument("--config-hash", default="<canonical param hash / cache schema version>")
    ap.add_argument("--spec", default="<spec label + decisive constants>")
    ap.add_argument("--seeds", default="<seeds, or 'deterministic'>")
    ap.add_argument("--artifacts", default="<path to heavy outputs (host if machine-local)>")
    ap.add_argument("--packages", default="", help="comma-separated package names to pin in the block")
    ap.add_argument("--mlflow", default="", help="optional: '<uri> exp=<name> runs=<id,...>'")
    ap.add_argument("--repo", default=".", help="repo root for git introspection (default: cwd)")
    ap.add_argument("--append", default=None, help="append the block to this file instead of stdout")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    sha = sh(["git", "rev-parse", "--short", "HEAD"], repo) or "<no git>"
    branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo) or "?"
    dirty_stat = sh(["git", "diff", "--stat", "HEAD"], repo)
    dirty = "yes" if dirty_stat else "no"

    py = f"python {sys.version.split()[0]}"
    env = py + (", " + pkg_versions([p.strip() for p in args.packages.split(",") if p.strip()])
                if args.packages else " (lockfile @ recorded SHA is the full answer)")

    lines = [
        "## Provenance",
        "",
        f"- **code**: `{sha}` (dirty: {dirty}) @ branch `{branch}`",
        f"- **repro**: `{args.cmd}`",
        f"- **data**: {args.data}",
        f"- **config-hash**: {getattr(args, 'config_hash')}",
        f"- **spec**: {args.spec}",
        f"- **seeds**: {args.seeds}",
        f"- **env**: {env}",
        f"- **artifacts**: {args.artifacts}",
    ]
    if args.mlflow:
        lines.append(f"- **mlflow**: {args.mlflow}")
    lines.append(f"- **recorded**: {dt.datetime.now().isoformat(timespec='seconds')} on {socket.gethostname()}")
    if dirty == "yes":
        lines += ["", "<!-- dirty working tree at record time:",
                  *("     " + ln for ln in dirty_stat.splitlines()[:20]), "-->",
                  "", "> WARNING: dirty tree — the SHA above does NOT reproduce this table.",
                  "> Commit first, then re-run the run of record."]

    block = "\n".join(lines) + "\n"
    if args.append:
        with open(args.append, "a", encoding="utf-8") as fh:
            fh.write("\n" + block)
        print(f"appended provenance block to {args.append}")
    else:
        print(block)


if __name__ == "__main__":
    main()
