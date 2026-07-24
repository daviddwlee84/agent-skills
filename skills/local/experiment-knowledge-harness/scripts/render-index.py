#!/usr/bin/env python3
"""Rebuild the experiment index + map in experiments/README.md and validate all surfaces.

Validates:
  - every REPORT.md front-matter (required keys, status enum, id/folder match,
    optional `refs: [#NNN, ...]` cross-references)
  - LEDGER.md finding syntax, lanes, and cross-refs (evidence #NNN, overturned-by)
  - ROADMAP.md lane order, item grammar, payoff/cat presence, depends-on refs
  - folders missing REPORT.md (warning: invisible to the index)

Then rewrites two sentinel blocks in README.md (unless --validate-only):
  - experiment-index: table sorted by experiment id (newest last)
  - experiment-map:   Mermaid big-picture graph — experiments (styled by
    status), baseline / refs / overturns edges, and queued ROADMAP items
    hanging off the findings they depend on. Missing map sentinels are
    auto-inserted above the index block (one-time upgrade for older READMEs).

Usage:
  render-index.py [--root DIR] [--validate-only] [--strict]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    EXP_REF_RE,
    INDEX_BEGIN,
    INDEX_END,
    MAP_BEGIN,
    MAP_END,
    Experiment,
    Ledger,
    RoadmapItem,
    iter_experiments,
    parse_ledger,
    parse_roadmap,
    report_problems,
    resolve_root,
    validate_experiments,
    validate_ledger_refs,
    validate_roadmap_refs,
)


def build_table(exps: list[Experiment], root: Path) -> str:
    if not exps:
        return "_No experiments yet — scaffold one with the skill's `new-experiment.py`._"
    rows = [
        "| # | title | status | axis | spec | started | concluded | findings | one-line conclusion |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in sorted(exps, key=lambda x: x.id):
        m = e.meta
        findings = ", ".join(str(f) for f in (m.get("findings") or [])) or "—"
        conclusion = str(m.get("conclusion") or "—").replace("|", "\\|")
        link = f"[#{e.id}]({e.folder.name}/REPORT.md)"
        rows.append(
            f"| {link} | {m.get('title', '')} | `{m.get('status', '')}` | {m.get('axis', '')} "
            f"| `{m.get('spec', '')}` | {m.get('started', '')} | {m.get('concluded') or '—'} "
            f"| {findings} | {conclusion} |"
        )
    return "\n".join(rows)


def _mermaid_label(s: str, limit: int = 34) -> str:
    s = str(s).replace('"', "'").strip()
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


def _compact_findings(fids: list[str]) -> str:
    """['F-001'..'F-005'] -> 'F-001..F-005'; non-contiguous -> comma join."""
    if not fids:
        return ""
    nums = sorted(int(f.split("-")[1]) for f in fids)
    if len(nums) > 2 and nums == list(range(nums[0], nums[-1] + 1)):
        return f"F-{nums[0]:03d}..F-{nums[-1]:03d}"
    return ", ".join(f"F-{n:03d}" for n in nums)


def build_map(exps: list[Experiment], ledger: Ledger, items: list[RoadmapItem]) -> str:
    """Mermaid flowchart: the whole research programme on one screen."""
    if not exps:
        return "_No experiments yet — the map appears after the first `new-experiment.py`._"

    exp_by_id = {f"#{e.id}": e for e in exps}
    finding_src = {f.fid: f.source for f in ledger.findings.values()}

    lines = ["```mermaid", "flowchart LR"]

    # --- experiment nodes, grouped visually by status class.
    for e in sorted(exps, key=lambda x: x.id):
        m = e.meta
        node = f"E{e.id}"
        fids = _compact_findings([str(f) for f in (m.get("findings") or [])])
        label_parts = [f"#{e.id} {_mermaid_label(m.get('title', ''), 30)}", str(m.get("status", "?"))]
        if fids:
            label_parts.append(fids)
        label = "<br/>".join(label_parts)
        lines.append(f'    {node}["{label}"]')
        lines.append(f'    click {node} "{e.folder.name}/REPORT.md"')
        status = str(m.get("status", ""))
        cls = {
            "concluded-success": "ok",
            "concluded-negative": "neg",
            "inconclusive": "mixed",
            "superseded": "old",
            "running": "run",
            "planned": "plan",
        }.get(status, "plan")
        lines.append(f"    class {node} {cls}")

    # --- experiment -> experiment edges.
    for e in sorted(exps, key=lambda x: x.id):
        node = f"E{e.id}"
        baseline_refs = {f"#{m}" for m in EXP_REF_RE.findall(str(e.meta.get("baseline", "")))}
        for ref in sorted(baseline_refs):
            if ref in exp_by_id and ref != f"#{e.id}":
                lines.append(f"    E{exp_by_id[ref].id} -. baseline .-> {node}")
        for ref in sorted(str(r) for r in (e.meta.get("refs") or [])):
            if ref in exp_by_id and ref != f"#{e.id}" and ref not in baseline_refs:
                lines.append(f"    E{exp_by_id[ref].id} -. ref .-> {node}")

    # --- overturn edges (belief evolution): new finding's exp ⊗ old finding's exp.
    for f in ledger.findings.values():
        if f.status == "overturned" and f.overturned_by:
            src_new = finding_src.get(f.overturned_by, "")
            if f.source.startswith("#") and src_new.startswith("#") and src_new != f.source:
                new_exp, old_exp = exp_by_id.get(src_new), exp_by_id.get(f.source)
                if new_exp and old_exp:
                    lines.append(
                        f'    E{new_exp.id} -- "{f.overturned_by} overturns {f.fid}" --> E{old_exp.id}'
                    )

    # --- queued ROADMAP items (active lanes), hanging off their dependencies.
    for qn, it in enumerate((i for i in items if i.lane != "## Done"), start=1):
        node = f"Q{qn}"
        lane = it.lane.replace("## ", "")
        lines.append(f'    {node}(["{lane} · {_mermaid_label(it.title, 36)}"])')
        lines.append(f"    class {node} queue")
        for d in it.depends_on:
            src = finding_src.get(d, d) if d.startswith("F-") else d
            if src in exp_by_id:
                label = d if d.startswith("F-") else "after"
                lines.append(f"    E{exp_by_id[src].id} -- {label} --> {node}")

    lines += [
        "    classDef ok fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20",
        "    classDef neg fill:#ffebee,stroke:#c62828,color:#b71c1c",
        "    classDef mixed fill:#fff8e1,stroke:#f9a825,color:#f57f17",
        "    classDef run fill:#e3f2fd,stroke:#1565c0,color:#0d47a1",
        "    classDef plan fill:#f5f5f5,stroke:#9e9e9e,color:#424242",
        "    classDef old fill:#eeeeee,stroke:#bdbdbd,color:#757575,stroke-dasharray: 5 5",
        "    classDef queue fill:#f3e5f5,stroke:#7b1fa2,color:#4a148c,stroke-dasharray: 3 3",
        "```",
        "",
        "_Legend: green = concluded-success · red = concluded-negative · amber ="
        " inconclusive · blue = running · grey = planned/superseded · dashed purple ="
        " queued ROADMAP item (edge label = the finding its priority rests on)._",
    ]
    return "\n".join(lines)


def splice_block(readme: Path, begin: str, end: str, content: str) -> bool:
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if begin not in text or end not in text:
        sys.exit(
            f"error: {readme} lacks sentinels {begin} / {end} — "
            "re-create it from assets/experiments-README.md.template"
        )
    head, rest = text.split(begin, 1)
    _, tail = rest.split(end, 1)
    new = f"{head}{begin}\n\n{content}\n\n{end}{tail}"
    if new != text:
        readme.write_text(new, encoding="utf-8")
        return True
    return False


def ensure_map_sentinels(readme: Path) -> None:
    """Upgrade path: insert the map block above the index block if absent."""
    text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if MAP_BEGIN in text and MAP_END in text:
        return
    if INDEX_BEGIN not in text:
        sys.exit(f"error: {readme} lacks {INDEX_BEGIN} — cannot place the map block")
    block = f"## Map\n\n{MAP_BEGIN}\n{MAP_END}\n\n## Index\n\n{INDEX_BEGIN}"
    readme.write_text(text.replace(INDEX_BEGIN, block, 1), encoding="utf-8")
    print(f"upgrade: inserted experiment-map sentinels into {readme.name}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="experiments root (default: auto-detect upward from cwd)")
    ap.add_argument("--validate-only", action="store_true", help="validate without rewriting the index")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    root = resolve_root(args.root)
    problems: list[str] = []

    exps = iter_experiments(root, problems)
    validate_experiments(root, exps, problems)
    ledger = parse_ledger(root / "LEDGER.md", problems)
    validate_ledger_refs(ledger, exps, problems)
    items = parse_roadmap(root / "ROADMAP.md", problems)
    validate_roadmap_refs(items, ledger, exps, problems)

    rc = report_problems(problems, strict=args.strict)
    if rc != 0:
        sys.exit(rc)

    if not args.validate_only:
        readme = root / "README.md"
        ensure_map_sentinels(readme)
        changed = splice_block(readme, INDEX_BEGIN, INDEX_END, build_table(exps, root))
        changed |= splice_block(readme, MAP_BEGIN, MAP_END, build_map(exps, ledger, items))
        print(f"index+map: {'updated' if changed else 'unchanged'} ({len(exps)} experiment(s))")


if __name__ == "__main__":
    main()
