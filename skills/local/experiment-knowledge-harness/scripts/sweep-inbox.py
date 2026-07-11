#!/usr/bin/env python3
"""Sweep experiments/INBOX.md — formalize raw human ideas into ROADMAP.md items.

The inbox is the zero-friction capture surface: humans drop `- ` bullets in
free text, optionally with `key=value` hints (lane=P2 effort=M cat=research
payoff="..." depends-on=F-003 title="..."). This script is the bridge to the
validator-checked ROADMAP grammar.

Modes:
  (default)          List entries with their parsed hints and, per entry, the
                     judgments still missing. This is the agent's question
                     list — ask the user, don't invent payoffs.
  --formalize N ...  Move entry N into ROADMAP.md. Missing judgments must be
                     supplied via flags (flags override inline hints). The
                     bullet is deleted from INBOX.md unless --keep.
  --batch            Formalize every entry whose judgments are already
                     complete (from hints alone); leave the rest untouched.

Required judgments per item: --lane P1|P2|P3|P? , --effort S|M|L|XL ,
--cat research|engineering|data|tooling|infra , --payoff "<value, with units>".
Optional: --title (defaults to first ~8 words of the idea), --desc (defaults
to the full idea text), --depends-on "F-003,#001".

Examples:
  sweep-inbox.py
  sweep-inbox.py --formalize 2 --lane P2 --effort M --cat research \
      --payoff "decides whether maker fills rescue thin-book symbols"
  sweep-inbox.py --batch
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    CAT_ENUM,
    EFFORTS,
    InboxEntry,
    format_roadmap_item,
    insert_roadmap_item,
    parse_inbox,
    parse_roadmap,
    remove_inbox_entry,
    resolve_root,
)

LANES = ("P1", "P2", "P3", "P?")
REQUIRED = ("lane", "effort", "cat", "payoff")

QUESTION_FOR = {
    "lane": "priority lane? (P1 next batch / P2 worth doing / P3 someday / P? needs a spike first)",
    "effort": "effort? (S <1h / M half-day-or-overnight / L multi-day / XL campaign)",
    "cat": f"category? one of {', '.join(CAT_ENUM)}",
    "payoff": "expected payoff, with units? (metric uplift / speedup / go-no-go decision / unblocks #NNN)",
}


def judgments(entry: InboxEntry, args: argparse.Namespace | None = None) -> dict[str, str | None]:
    """Merge inline hints with CLI flags (flags win)."""
    j: dict[str, str | None] = {k: entry.hints.get(k) for k in ("lane", "effort", "cat", "payoff", "title")}
    j["depends-on"] = entry.hints.get("depends-on")
    if args is not None:
        for key, val in (
            ("lane", args.lane),
            ("effort", args.effort),
            ("cat", args.cat),
            ("payoff", args.payoff),
            ("title", args.title),
            ("depends-on", args.depends_on),
        ):
            if val:
                j[key] = val
    return j


def default_title(text: str, max_words: int = 8) -> str:
    words = text.split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


def list_entries(entries: list[InboxEntry]) -> None:
    if not entries:
        print("inbox is empty — nothing to sweep")
        return
    for e in entries:
        j = judgments(e)
        missing = [k for k in REQUIRED if not j.get(k)]
        print(f"[{e.n}] {e.text or e.raw}")
        known = {k: v for k, v in j.items() if v}
        if known:
            print(f"    hints: {known}")
        if missing:
            print("    ASK THE USER:")
            for k in missing:
                print(f"      - {QUESTION_FOR[k]}")
        else:
            print("    complete — ready for --formalize/--batch")
        print()


def formalize(root: Path, inbox: Path, entry: InboxEntry, j: dict[str, str | None], *, keep: bool) -> None:
    for k in REQUIRED:
        if not j.get(k):
            sys.exit(f"error: entry [{entry.n}] missing `{k}` — supply --{k} (question: {QUESTION_FOR[k]})")
    lane, effort, cat = str(j["lane"]), str(j["effort"]), str(j["cat"])
    if lane not in LANES:
        sys.exit(f"error: lane {lane!r} not in {LANES}")
    if effort not in EFFORTS:
        sys.exit(f"error: effort {effort!r} not in {EFFORTS}")
    if cat not in CAT_ENUM:
        sys.exit(f"error: cat {cat!r} not in {CAT_ENUM}")
    deps = [d.strip() for d in str(j.get("depends-on") or "").split(",") if d.strip()]
    title = str(j.get("title") or default_title(entry.text or entry.raw))
    desc = str(j.get("desc") or entry.text or entry.raw)

    roadmap = root / "ROADMAP.md"
    before = roadmap.read_text(encoding="utf-8")
    item = format_roadmap_item(
        lane=lane, effort=effort, title=title, desc=desc, payoff=str(j["payoff"]), cat=cat, depends_on=deps
    )
    insert_roadmap_item(roadmap, lane, item)

    problems: list[str] = []
    parse_roadmap(roadmap, problems)
    errors = [p for p in problems if p.startswith("error:")]
    if errors:
        roadmap.write_text(before, encoding="utf-8")  # revert
        for p in errors:
            print(p, file=sys.stderr)
        sys.exit(f"error: formalized item failed ROADMAP validation — reverted ({len(errors)} error(s))")

    if not keep:
        remove_inbox_entry(inbox, entry)
    print(f"formalized [{entry.n}] -> ROADMAP ## {lane}:")
    print("  " + item.replace("\n", "\n  "))
    if not keep:
        print("  (bullet removed from INBOX.md)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="experiments root (default: auto-detect)")
    ap.add_argument("--formalize", type=int, metavar="N", help="entry number to formalize (see default listing)")
    ap.add_argument("--batch", action="store_true", help="formalize all hint-complete entries")
    ap.add_argument("--lane", choices=LANES)
    ap.add_argument("--effort", choices=EFFORTS)
    ap.add_argument("--cat", choices=CAT_ENUM)
    ap.add_argument("--payoff", help="expected value, with units (mandatory judgment)")
    ap.add_argument("--title", help="ROADMAP item title (default: first words of the idea)")
    ap.add_argument("--desc", help="item description (default: the raw idea text)")
    ap.add_argument("--depends-on", dest="depends_on", help="comma-separated F-NNN / #NNN refs")
    ap.add_argument("--keep", action="store_true", help="don't delete the swept bullet from INBOX.md")
    args = ap.parse_args()

    root = resolve_root(args.root)
    inbox = root / "INBOX.md"
    entries = parse_inbox(inbox)

    if args.formalize is not None and args.batch:
        sys.exit("error: --formalize and --batch are mutually exclusive")

    if args.formalize is not None:
        matches = [e for e in entries if e.n == args.formalize]
        if not matches:
            sys.exit(f"error: no inbox entry [{args.formalize}] (have 1..{len(entries)})")
        j = judgments(matches[0], args)
        if args.desc:
            j["desc"] = args.desc
        formalize(root, inbox, matches[0], j, keep=args.keep)
        return

    if args.batch:
        done = 0
        # Re-parse after each removal: line numbers shift.
        while True:
            entries = parse_inbox(inbox)
            ready = next((e for e in entries if all(judgments(e).get(k) for k in REQUIRED)), None)
            if ready is None:
                break
            formalize(root, inbox, ready, judgments(ready), keep=False)
            done += 1
        left = len(parse_inbox(inbox))
        print(f"batch: {done} formalized, {left} left in inbox (incomplete judgments — run the default listing)")
        return

    list_entries(entries)


if __name__ == "__main__":
    main()
