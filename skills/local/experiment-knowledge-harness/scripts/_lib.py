"""Shared parsing/validation helpers for experiment-knowledge-harness scripts.

Stdlib only. All surfaces are plain Markdown with narrow, regex-checkable
grammars — see the skill's references/ docs for the authoritative specs.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

STATUS_ENUM = (
    "planned",
    "running",
    "concluded-success",
    "concluded-negative",
    "inconclusive",
    "superseded",
)
CONCLUDED_STATUSES = ("concluded-success", "concluded-negative", "inconclusive", "superseded")
CAT_ENUM = ("research", "engineering", "data", "tooling", "infra")
EFFORTS = ("S", "M", "L", "XL")

INDEX_BEGIN = "<!-- experiment-index:begin -->"
INDEX_END = "<!-- experiment-index:end -->"
MAP_BEGIN = "<!-- experiment-map:begin -->"
MAP_END = "<!-- experiment-map:end -->"

REQUIRED_META = ("id", "slug", "title", "status", "question", "axis", "baseline", "spec", "started")

EXP_REF_RE = re.compile(r"#(\d{3,})")


def resolve_root(explicit: str | None) -> Path:
    """Locate the experiments root (the dir holding LEDGER.md + ROADMAP.md)."""
    if explicit:
        root = Path(explicit).resolve()
        if not (root / "LEDGER.md").exists():
            sys.exit(f"error: {root} does not look like an experiments root (no LEDGER.md)")
        return root
    cur = Path.cwd()
    for base in [cur, *cur.parents]:
        for cand in (base / "experiments", base):
            if (cand / "LEDGER.md").exists() and (cand / "ROADMAP.md").exists():
                return cand
    sys.exit("error: could not find an experiments root (LEDGER.md + ROADMAP.md); pass --root")


# ---------------------------------------------------------------- front-matter

def parse_front_matter(text: str, *, path: Path | None = None) -> dict[str, object]:
    """Minimal YAML subset: flat `key: value`, inline [a, b] lists, `>` folds."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing front-matter opening '---'")
    meta: dict[str, object] = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            return meta
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            raise ValueError(f"{path}: unparseable front-matter line: {line!r}")
        key, raw = m.group(1), m.group(2).strip()
        if raw == ">":
            folded: list[str] = []
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                if lines[i].strip() == "---":
                    break
                folded.append(lines[i].strip())
                i += 1
            meta[key] = " ".join(x for x in folded if x)
        elif raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            meta[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()] if inner else []
        else:
            meta[key] = raw.strip("'\"")
    raise ValueError(f"{path}: front-matter never closed with '---'")


# ---------------------------------------------------------------- experiments

@dataclass
class Experiment:
    folder: Path
    meta: dict[str, object]

    @property
    def id(self) -> str:
        return str(self.meta.get("id", ""))


def iter_experiments(root: Path, problems: list[str] | None = None) -> list[Experiment]:
    exps: list[Experiment] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        if d.name == "__pycache__":
            continue
        report = d / "REPORT.md"
        if not report.exists():
            if problems is not None:
                problems.append(
                    f"warning: {d.relative_to(root)}/ has no REPORT.md — invisible to the index (will be re-run by someone)"
                )
            continue
        try:
            meta = parse_front_matter(report.read_text(encoding="utf-8"), path=report)
        except ValueError as e:
            if problems is not None:
                problems.append(f"error: {e}")
            continue
        exps.append(Experiment(folder=d, meta=meta))
    return exps


def validate_experiments(root: Path, exps: list[Experiment], problems: list[str]) -> None:
    seen_ids: dict[str, str] = {}
    for exp in exps:
        rel = exp.folder.name
        meta = exp.meta
        for key in REQUIRED_META:
            if not str(meta.get(key, "")).strip():
                problems.append(f"error: {rel}/REPORT.md front-matter missing `{key}:`")
        eid = str(meta.get("id", ""))
        if eid:
            if not re.fullmatch(r"\d{3,}", eid):
                problems.append(f"error: {rel}: id `{eid}` must be zero-padded digits (e.g. 001)")
            if eid in seen_ids:
                problems.append(f"error: duplicate experiment id #{eid} in {rel} and {seen_ids[eid]}")
            seen_ids[eid] = rel
            if not rel.startswith(f"{eid}-"):
                problems.append(f"error: {rel}: folder name must start with `{eid}-`")
            slug = str(meta.get("slug", ""))
            if slug and rel != f"{eid}-{slug}":
                problems.append(f"warning: {rel}: folder != `{eid}-{slug}` from front-matter slug")
        status = str(meta.get("status", ""))
        if status and status not in STATUS_ENUM:
            problems.append(f"error: {rel}: status `{status}` not in {STATUS_ENUM}")
        if status in CONCLUDED_STATUSES:
            for key in ("concluded", "conclusion"):
                if not str(meta.get(key, "")).strip():
                    problems.append(f"error: {rel}: status `{status}` requires `{key}:` in front-matter")
        for f in meta.get("findings", []) or []:
            if not re.fullmatch(r"F-\d{3,}", str(f)):
                problems.append(f"error: {rel}: findings entry `{f}` is not an F-NNN id")
        for r in meta.get("refs", []) or []:
            if not re.fullmatch(r"#\d{3,}", str(r)):
                problems.append(f"error: {rel}: refs entry `{r}` is not an #NNN id")

    all_ids = {f"#{e.id}" for e in exps}
    for exp in exps:
        for r in exp.meta.get("refs", []) or []:
            if str(r) not in all_ids:
                problems.append(f"error: {exp.folder.name}: refs `{r}` matches no experiment")
            elif str(r) == f"#{exp.id}":
                problems.append(f"warning: {exp.folder.name}: refs itself")


# ---------------------------------------------------------------- ledger

ACTIVE_RE = re.compile(r"^- \*\*(F-\d{3,})\*\* \[(\d{4}-\d{2}-\d{2})\] \((#\d{3,}|ext)\) (.+)$")
OVERTURNED_RE = re.compile(r"^- ~~\*\*(F-\d{3,})\*\*~~ \[(\d{4}-\d{2}-\d{2})\] \((#\d{3,}|ext)\) (.+)$")
WEAKENED_RE = re.compile(r"\(weakened by (F-\d{3,})\)")
OVERTURN_NOTE_RE = re.compile(r"overturned \d{4}-\d{2}-\d{2} by (F-\d{3,})")


@dataclass
class Finding:
    fid: str
    date: str
    source: str  # "#NNN" or "ext"
    text: str
    status: str  # active | weakened | overturned
    weakened_by: str | None = None
    overturned_by: str | None = None


@dataclass
class Ledger:
    path: Path
    findings: dict[str, Finding] = field(default_factory=dict)


def _collect_items(lines: list[str], start: int, end: int) -> list[tuple[int, str]]:
    """Group a lane's lines into (first_line_no, full_item_text) tuples.

    An item starts with `- ` at column 0; subsequent indented / plain
    continuation lines are folded into it. Non-item prose between items is
    ignored (matching the TODO-harness validator behaviour).
    """
    items: list[tuple[int, str]] = []
    cur: list[str] | None = None
    cur_no = 0
    for no in range(start, end):
        line = lines[no]
        if line.startswith("- "):
            if cur is not None:
                items.append((cur_no, " ".join(cur)))
            cur = [line.rstrip()]
            cur_no = no + 1
        elif cur is not None and (line.startswith(("  ", "\t")) and line.strip()):
            cur.append(line.strip())
        else:
            if cur is not None:
                items.append((cur_no, " ".join(cur)))
                cur = None
    if cur is not None:
        items.append((cur_no, " ".join(cur)))
    return items


def _lane_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
        elif start is not None and line.startswith("## "):
            return (start, i)
    return (start, len(lines)) if start is not None else None


def parse_ledger(path: Path, problems: list[str] | None = None) -> Ledger:
    ledger = Ledger(path=path)
    if not path.exists():
        if problems is not None:
            problems.append(f"error: {path} not found")
        return ledger
    lines = path.read_text(encoding="utf-8").splitlines()
    probs = problems if problems is not None else []

    for heading, active in (("## Active", True), ("## Overturned", False)):
        bounds = _lane_bounds(lines, heading)
        if bounds is None:
            probs.append(f"error: {path.name}: missing `{heading}` section")
            continue
        for line_no, item in _collect_items(lines, *bounds):
            m = (ACTIVE_RE if active else OVERTURNED_RE).match(item)
            if not m:
                other = (OVERTURNED_RE if active else ACTIVE_RE).match(item)
                if other:
                    probs.append(f"error: {path.name}:{line_no}: finding is in the wrong lane for its syntax")
                else:
                    probs.append(f"error: {path.name}:{line_no}: unparseable finding line: {item[:80]!r}")
                continue
            fid, date, source, text = m.groups()
            if fid in ledger.findings:
                probs.append(f"error: {path.name}:{line_no}: duplicate finding id {fid}")
            status = "active" if active else "overturned"
            weakened_by = overturned_by = None
            if active:
                wm = WEAKENED_RE.search(text)
                if wm:
                    status, weakened_by = "weakened", wm.group(1)
            else:
                om = OVERTURN_NOTE_RE.search(text)
                if om:
                    overturned_by = om.group(1)
                else:
                    probs.append(
                        f"error: {path.name}:{line_no}: {fid} in Overturned lane lacks "
                        f"`overturned YYYY-MM-DD by F-NNN` annotation"
                    )
            ledger.findings[fid] = Finding(fid, date, source, text, status, weakened_by, overturned_by)
    return ledger


def validate_ledger_refs(ledger: Ledger, exps: list[Experiment], problems: list[str]) -> None:
    exp_ids = {f"#{e.id}" for e in exps}
    for f in ledger.findings.values():
        if f.source != "ext" and f.source not in exp_ids:
            problems.append(f"error: LEDGER {f.fid}: evidence {f.source} matches no experiment folder")
        for ref_attr in ("weakened_by", "overturned_by"):
            ref = getattr(f, ref_attr)
            if ref and ref not in ledger.findings:
                problems.append(f"error: LEDGER {f.fid}: {ref_attr.replace('_', ' ')} {ref} does not exist")
    for exp in exps:
        for fid in exp.meta.get("findings", []) or []:
            if str(fid) not in ledger.findings:
                problems.append(
                    f"error: {exp.folder.name}: front-matter lists finding {fid} not present in LEDGER.md"
                )


# ---------------------------------------------------------------- roadmap

LANES = ("## P1", "## P2", "## P3", "## P?", "## Done")
ACTIVE_ITEM_RE = re.compile(r"^- \[ \] \*\*\[(\?/)?(S|M|L|XL)\] (.+?)\*\* — (.+)$")
DONE_ITEM_RE = re.compile(r"^- ✅ \[(\d{4}-\d{2}-\d{2})\] \[P[123?]/(S|M|L|XL)\] (.+)$")
DEPENDS_RE = re.compile(r"depends-on:\s*([^;)]+)")
CAT_RE = re.compile(r"cat:\s*([a-z]+)")


@dataclass
class RoadmapItem:
    lane: str
    line_no: int
    title: str
    text: str
    depends_on: list[str] = field(default_factory=list)


def parse_roadmap(path: Path, problems: list[str] | None = None) -> list[RoadmapItem]:
    items: list[RoadmapItem] = []
    if not path.exists():
        if problems is not None:
            problems.append(f"error: {path} not found")
        return items
    lines = path.read_text(encoding="utf-8").splitlines()
    probs = problems if problems is not None else []

    positions = [i for i, ln in enumerate(lines) if ln.strip() in LANES]
    ordered = [lines[i].strip() for i in positions]
    if ordered != [x for x in LANES if x in ordered]:
        probs.append(f"error: ROADMAP lanes out of order: {ordered} (expected subset order of {LANES})")
    missing = [x for x in LANES if x not in ordered]
    if missing:
        probs.append(f"error: ROADMAP missing lanes: {missing}")

    for lane in LANES:
        bounds = _lane_bounds(lines, lane)
        if bounds is None:
            continue
        for line_no, item in _collect_items(lines, *bounds):
            if lane == "## Done":
                if not DONE_ITEM_RE.match(item):
                    probs.append(f"error: ROADMAP:{line_no}: bad Done syntax: {item[:80]!r}")
                continue
            m = ACTIVE_ITEM_RE.match(item)
            if not m:
                probs.append(f"error: ROADMAP:{line_no}: bad item syntax: {item[:80]!r}")
                continue
            spike, _effort, title, _desc = m.groups()
            if lane == "## P?" and not spike:
                probs.append(f"error: ROADMAP:{line_no}: P? items must use [?/Effort]: {title!r}")
            if lane != "## P?" and spike:
                probs.append(f"error: ROADMAP:{line_no}: [?/Effort] only allowed in P?: {title!r}")
            if "payoff:" not in item:
                probs.append(f"error: ROADMAP:{line_no}: missing `payoff:` — {title!r}")
            cm = CAT_RE.search(item)
            if not cm:
                probs.append(f"error: ROADMAP:{line_no}: missing `cat:` — {title!r}")
            elif cm.group(1) not in CAT_ENUM:
                probs.append(f"error: ROADMAP:{line_no}: cat `{cm.group(1)}` not in {CAT_ENUM}")
            deps: list[str] = []
            dm = DEPENDS_RE.search(item)
            if dm:
                deps = [d.strip() for d in dm.group(1).split(",") if d.strip()]
                for d in deps:
                    if not re.fullmatch(r"F-\d{3,}|#\d{3,}", d):
                        probs.append(f"error: ROADMAP:{line_no}: bad depends-on ref `{d}`")
            items.append(RoadmapItem(lane=lane, line_no=line_no, title=title, text=item, depends_on=deps))
    return items


def validate_roadmap_refs(
    items: list[RoadmapItem], ledger: Ledger, exps: list[Experiment], problems: list[str]
) -> None:
    exp_ids = {f"#{e.id}" for e in exps}
    for it in items:
        for d in it.depends_on:
            if d.startswith("F-") and d not in ledger.findings:
                problems.append(f"error: ROADMAP `{it.title}`: depends-on {d} not in LEDGER.md")
            if d.startswith("#") and d not in exp_ids:
                problems.append(f"error: ROADMAP `{it.title}`: depends-on {d} matches no experiment")


# ---------------------------------------------------------------- inbox

INBOX_HINT_KEYS = ("lane", "effort", "cat", "payoff", "depends-on", "title")


@dataclass
class InboxEntry:
    n: int  # 1-based entry number (stable within one sweep session)
    line_no: int  # first line of the bullet in INBOX.md
    raw: str  # full folded bullet text (without leading "- ")
    text: str  # raw minus recognised key=value hints
    hints: dict[str, str] = field(default_factory=dict)


def _parse_hints(raw: str) -> tuple[str, dict[str, str]]:
    """Split `key=value` hint tokens out of a free-text idea line.

    Values may be double-quoted to contain spaces:
    ``payoff="decides go/no-go" cat=research``. Unrecognised keys are left
    in the prose untouched.
    """
    hints: dict[str, str] = {}
    keys = "|".join(re.escape(k) for k in INBOX_HINT_KEYS)
    pat = re.compile(rf'\b({keys})=("([^"]*)"|\S+)')

    def _grab(m: re.Match) -> str:
        hints[m.group(1)] = m.group(3) if m.group(3) is not None else m.group(2)
        return ""

    text = pat.sub(_grab, raw)
    return re.sub(r"\s{2,}", " ", text).strip(" —-\t"), hints


def parse_inbox(path: Path) -> list[InboxEntry]:
    """Collect idea bullets from INBOX.md (prose / comments / headings ignored)."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[InboxEntry] = []
    for line_no, item in _collect_items(lines, 0, len(lines)):
        raw = item[2:].strip()  # strip "- "
        if not raw:
            continue
        text, hints = _parse_hints(raw)
        entries.append(InboxEntry(n=len(entries) + 1, line_no=line_no, raw=raw, text=text, hints=hints))
    return entries


def remove_inbox_entry(path: Path, entry: InboxEntry) -> None:
    """Delete one bullet (with its continuation lines) from INBOX.md."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = entry.line_no - 1
    if start >= len(lines) or not lines[start].startswith("- "):
        raise ValueError(f"{path}:{entry.line_no}: expected a bullet here — INBOX changed since parse?")
    end = start + 1
    while end < len(lines) and lines[end].startswith(("  ", "\t")) and lines[end].strip():
        end += 1
    del lines[start:end]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


# ---------------------------------------------------------------- roadmap writing

def format_roadmap_item(
    *,
    lane: str,
    effort: str,
    title: str,
    desc: str,
    payoff: str,
    cat: str,
    depends_on: list[str] | None = None,
    width: int = 78,
) -> str:
    """Render a canonical (validator-passing) active ROADMAP item, wrapped."""
    import textwrap

    if lane not in ("P1", "P2", "P3", "P?"):
        raise ValueError(f"lane must be P1/P2/P3/P?, got {lane!r}")
    if effort not in EFFORTS:
        raise ValueError(f"effort must be one of {EFFORTS}, got {effort!r}")
    if cat not in CAT_ENUM:
        raise ValueError(f"cat must be one of {CAT_ENUM}, got {cat!r}")
    for d in depends_on or []:
        if not re.fullmatch(r"F-\d{3,}|#\d{3,}", d):
            raise ValueError(f"bad depends-on ref {d!r} (want F-NNN or #NNN)")
    tag = f"[?/{effort}]" if lane == "P?" else f"[{effort}]"
    tail = f"payoff: {payoff}; cat: {cat}"
    if depends_on:
        tail += f"; depends-on: {', '.join(depends_on)}"
    body = f"- [ ] **{tag} {title}** — {desc.rstrip('.')} ({tail})"
    return textwrap.fill(body, width=width, subsequent_indent="  ", break_long_words=False, break_on_hyphens=False)


def insert_roadmap_item(path: Path, lane: str, item_text: str) -> None:
    """Append ``item_text`` at the end of the ``## <lane>`` section."""
    lines = path.read_text(encoding="utf-8").splitlines()
    bounds = _lane_bounds(lines, f"## {lane}")
    if bounds is None:
        raise ValueError(f"{path}: lane `## {lane}` not found")
    start, end = bounds
    insert_at = end
    while insert_at > start and not lines[insert_at - 1].strip():
        insert_at -= 1
    block = item_text.splitlines()
    if lines[insert_at - 1].strip():  # keep one blank line between items/prose
        block = ["", *block]
    lines[insert_at:insert_at] = block
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- reporting

def report_problems(problems: list[str], *, strict: bool = False) -> int:
    errors = [p for p in problems if p.startswith("error:")]
    warnings = [p for p in problems if not p.startswith("error:")]
    for p in warnings:
        print(p, file=sys.stderr)
    for p in errors:
        print(p, file=sys.stderr)
    if errors or (strict and warnings):
        print(f"\nvalidation FAILED ({len(errors)} error(s), {len(warnings)} warning(s))", file=sys.stderr)
        return 1
    print(f"validation OK ({len(warnings)} warning(s))")
    return 0
