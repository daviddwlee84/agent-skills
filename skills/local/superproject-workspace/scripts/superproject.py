#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Keep a git-submodule superproject on track.

A gitlink records a commit, not a branch, so a superproject drifts by design.
This CLI makes the drift visible and moves pointers according to a
per-submodule policy stored as extra keys in `.gitmodules`:

    [submodule "app"]
        path = app
        url = git@github.com:me/app.git
        branch = main        # tracking branch (native git key)
        x-policy = track     # track | pin | lazy
        x-bump = pr          # pr | direct | manual   (only meaningful for track)
        x-tier = core        # free-form grouping
        update = none        # set for lazy children (native git key)

Stdlib only. Results go to stdout (text, or JSON with --json); diagnostics go
to stderr. Exit codes: 0 ok, 1 refused / check failed, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

__version__ = "0.2.0"

POLICIES = ("track", "pin", "lazy")
BUMP_MODES = ("pr", "direct", "manual")
WORKTREE_DIR = ".worktrees"

AGENTS_BEGIN = "<!-- superproject-workspace:agent-guidance -->"
AGENTS_END = "<!-- superproject-workspace:agent-guidance --> (end)"
JUST_BEGIN = "# superproject-workspace:begin"
JUST_END = "# superproject-workspace:end"
VENDORED_CLI = "scripts/superproject.py"

SKILL_ASSETS = Path(__file__).resolve().parent.parent / "assets"
GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}


class Refused(Exception):
    """A safety rule declined the operation; the message says why."""


class UsageError(Exception):
    pass


# ---------------------------------------------------------------- git helpers

def git(*args: str, cwd: Path, check: bool = True, input: str | None = None) -> str:
    p = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, env=GIT_ENV, input=input
    )
    if check and p.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed in {cwd}: {p.stderr.strip()}")
    return p.stdout.rstrip("\n")


def git_rc(*args: str, cwd: Path) -> int:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, env=GIT_ENV).returncode


def is_ancestor(repo: Path, a: str, b: str) -> bool | None:
    """True/False, or None when either object is unknown locally."""
    rc = git_rc("merge-base", "--is-ancestor", a, b, cwd=repo)
    return {0: True, 1: False}.get(rc)


def has_commit(repo: Path, sha: str) -> bool:
    return git_rc("cat-file", "-e", f"{sha}^{{commit}}", cwd=repo) == 0


def ref_exists(repo: Path, ref: str) -> bool:
    return git_rc("show-ref", "--verify", "--quiet", ref, cwd=repo) == 0


def remote_refs_containing(repo: Path, sha: str) -> list[str]:
    out = git("for-each-ref", "--contains", sha, "--format=%(refname:short)", "refs/remotes/origin",
              cwd=repo, check=False)
    return [r for r in out.splitlines() if r and r != "origin/HEAD"]


def tracked_dirty(repo: Path) -> int:
    out = git("status", "--porcelain", "--untracked-files=no", cwd=repo, check=False)
    return len([line for line in out.splitlines() if line.strip()])


def short(sha: str | None) -> str:
    return sha[:7] if sha else "-"


# ---------------------------------------------------------------- model

@dataclass
class Sub:
    name: str
    path: str
    url: str | None
    branch: str | None
    policy: str | None
    bump: str | None
    tier: str | None
    update: str | None

    @property
    def eff_policy(self) -> str:
        # An undeclared policy is treated as pin: never moved implicitly.
        return self.policy if self.policy in POLICIES else "pin"

    @property
    def eff_bump(self) -> str:
        if self.eff_policy != "track":
            return "manual"
        return self.bump if self.bump in BUMP_MODES else "manual"

    def eff_branch(self, root: Path) -> str:
        if self.branch == ".":
            return git("symbolic-ref", "-q", "--short", "HEAD", cwd=root, check=False) or "main"
        if self.branch:
            return self.branch
        # Undeclared: follow the child's remote default (main, master, ...).
        head = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", cwd=root / self.path, check=False)
        return head.removeprefix("origin/") if head.startswith("origin/") else "main"


def find_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).resolve()
        if not (root / ".gitmodules").exists():
            raise UsageError(f"{root} has no .gitmodules")
        return root
    cwd = Path.cwd()
    for cand in (
        git("rev-parse", "--show-superproject-working-tree", cwd=cwd, check=False),
        git("rev-parse", "--show-toplevel", cwd=cwd, check=False),
    ):
        if cand and (Path(cand) / ".gitmodules").exists():
            return Path(cand).resolve()
    # Inside a child worktree under .worktrees/: walk up to the superproject.
    for base in [cwd, *cwd.parents]:
        if (base / ".gitmodules").exists() and (base / ".git").exists():
            return base.resolve()
    raise UsageError("not inside a superproject (no .gitmodules found); pass --root")


def load_subs(root: Path) -> list[Sub]:
    if not (root / ".gitmodules").exists():
        return []
    out = subprocess.run(
        ["git", "config", "-z", "-f", ".gitmodules", "--get-regexp", r"^submodule\."],
        cwd=root, capture_output=True, text=True, env=GIT_ENV,
    ).stdout
    entries: dict[str, dict[str, str]] = {}
    for rec in out.split("\0"):
        if not rec:
            continue
        key, _, value = rec.partition("\n")
        name, _, var = key[len("submodule."):].rpartition(".")
        entries.setdefault(name, {})[var.lower()] = value
    return [
        Sub(
            name=name, path=e["path"].rstrip("/"), url=e.get("url"), branch=e.get("branch"),
            policy=e.get("x-policy"), bump=e.get("x-bump"), tier=e.get("x-tier"),
            update=e.get("update"),
        )
        for name, e in entries.items()
        if "path" in e
    ]


def gitlink(root: Path, path: str, tree: str = "HEAD") -> str | None:
    out = git("ls-tree", tree, "--", path, cwd=root, check=False)
    m = re.match(r"160000 commit ([0-9a-f]+)\t", out)
    return m.group(1) if m else None


def index_gitlink(root: Path, path: str) -> str | None:
    out = git("ls-files", "-s", "--", path, cwd=root, check=False)
    m = re.match(r"160000 ([0-9a-f]+) 0\t", out)
    return m.group(1) if m else None


def is_initialized(root: Path, sub: Sub) -> bool:
    p = root / sub.path
    if not (p / ".git").exists():
        return False
    top = git("rev-parse", "--show-toplevel", cwd=p, check=False)
    return bool(top) and Path(top).resolve() == p.resolve()


def fetch(repo: Path) -> str | None:
    p = subprocess.run(
        ["git", "fetch", "--prune", "--quiet", "origin"],
        cwd=repo, capture_output=True, text=True, env=GIT_ENV,
    )
    return None if p.returncode == 0 else p.stderr.strip() or "fetch failed"


def resolve(subs: list[Sub], ident: str) -> Sub:
    ident = ident.rstrip("/")
    hits = [s for s in subs if ident in (s.name, s.path)]
    if not hits:
        hits = [s for s in subs if Path(s.path).name == ident]
    if len(hits) != 1:
        known = ", ".join(s.name for s in subs)
        raise UsageError(f"{'ambiguous' if hits else 'unknown'} submodule {ident!r} (known: {known})")
    return hits[0]


def select(subs: list[Sub], args: argparse.Namespace, default) -> list[Sub]:
    names = getattr(args, "names", None) or []
    if names:
        chosen = [resolve(subs, n) for n in names]
    elif any(getattr(args, k, None) for k in ("tier", "policy")):
        chosen = list(subs)
    else:
        chosen = [s for s in subs if default(s)]
    if getattr(args, "tier", None):
        chosen = [s for s in chosen if s.tier == args.tier]
    if getattr(args, "policy", None):
        chosen = [s for s in chosen if s.eff_policy == args.policy]
    if getattr(args, "mode", None):
        chosen = [s for s in chosen if s.eff_bump == args.mode]
    return chosen


def sub_state(root: Path, sub: Sub, *, do_fetch: bool = False) -> dict:
    p = root / sub.path
    branch = sub.eff_branch(root)
    st: dict = {
        "name": sub.name, "path": sub.path, "policy": sub.policy, "bump": sub.eff_bump,
        "tier": sub.tier, "branch": branch, "recorded": gitlink(root, sub.path),
        "staged": None, "initialized": is_initialized(root, sub), "warnings": [],
    }
    staged = index_gitlink(root, sub.path)
    if staged and staged != st["recorded"]:
        st["staged"] = staged
    if not st["initialized"]:
        return st
    if do_fetch and (err := fetch(p)):
        st["warnings"].append(f"fetch failed: {err}")
    head = git("rev-parse", "HEAD", cwd=p, check=False) or None
    upstream = f"refs/remotes/origin/{branch}"
    st.update(
        head=head,
        checkout_branch=git("symbolic-ref", "-q", "--short", "HEAD", cwd=p, check=False) or None,
        dirty=tracked_dirty(p),
        drift=bool(head and st["recorded"] and head != st["recorded"]),
        upstream_exists=ref_exists(p, upstream),
        lag=None, unpushed=None, recorded_reachable=None, recorded_on_remote=None, head_reachable=None,
        worktrees=list_child_worktrees(root, sub),
    )
    if not st["upstream_exists"]:
        st["warnings"].append(f"origin/{branch} missing locally (fetch, or fix `branch`)")
        return st
    rec = st["recorded"]
    if rec and has_commit(p, rec):
        left, right = git("rev-list", "--left-right", "--count", f"{rec}...{upstream}", cwd=p).split()
        st.update(unpushed=int(left), lag=int(right), recorded_reachable=int(left) == 0)
        st["recorded_on_remote"] = st["recorded_reachable"] or bool(remote_refs_containing(p, rec))
    elif rec:
        st["warnings"].append(f"recorded commit {short(rec)} not present locally (fetch?)")
    if head:
        st["head_reachable"] = is_ancestor(p, head, upstream)
    return st


def list_child_worktrees(root: Path, sub: Sub) -> list[dict]:
    p = root / sub.path
    base = (root / WORKTREE_DIR).resolve()
    out = git("worktree", "list", "--porcelain", cwd=p, check=False)
    found = []
    for block in out.split("\n\n"):
        info: dict = {}
        for line in block.splitlines():
            k, _, v = line.partition(" ")
            info[k] = v or True
        wt = info.get("worktree")
        if not isinstance(wt, str) or not Path(wt).resolve().is_relative_to(base):
            continue
        br = info.get("branch")
        found.append({
            "path": str(Path(wt).resolve().relative_to(root.resolve())),
            "branch": br.removeprefix("refs/heads/") if isinstance(br, str) else None,
            "head": info.get("HEAD"),
            "prunable": "prunable" in info,
        })
    branch = sub.eff_branch(root)
    for wt in found:
        wt["merged"] = bool(
            wt["head"] and wt["branch"] != branch
            and is_ancestor(p, wt["head"], f"refs/remotes/origin/{branch}")
        )
        if not wt["prunable"] and (root / wt["path"]).exists():
            wt["dirty"] = tracked_dirty(root / wt["path"])
    return found


def emit(args: argparse.Namespace, data, text: str) -> None:
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(text)


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    return "\n".join("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows)


# ---------------------------------------------------------------- status

def describe(st: dict) -> tuple[str, str]:
    if not st["initialized"]:
        return "uninit", ""
    bits = []
    if st["checkout_branch"]:
        bits.append(f"on {st['checkout_branch']}")
    else:
        bits.append("detached")
    if st["dirty"]:
        bits.append(f"dirty({st['dirty']})")
    if st["drift"]:
        bits.append(f"head {short(st['head'])} != gitlink")
    if st["staged"]:
        bits.append(f"staged {short(st['staged'])}")
    if st["recorded_on_remote"] is False:
        bits.append("gitlink NOT on any origin branch")
    elif st["recorded_reachable"] is False:
        bits.append(f"gitlink off origin/{st['branch']} (on another origin branch)")
    if st["worktrees"]:
        bits.append(f"{len(st['worktrees'])} worktree(s)")
    bits += st["warnings"]
    lag = "-" if st["lag"] is None else str(st["lag"])
    return lag, "; ".join(bits)


def cmd_status(root: Path, subs: list[Sub], args) -> int:
    chosen = select(subs, args, lambda s: True)
    states = [sub_state(root, s, do_fetch=args.fetch) for s in chosen]
    rows = [["NAME", "POLICY", "BUMP", "TIER", "GITLINK", "LAG", "STATE"]]
    for st in states:
        lag, note = describe(st)
        rows.append([
            st["name"] if st["name"] == st["path"] else f"{st['name']} ({st['path']})",
            st["policy"] or "(unset)", st["bump"], st["tier"] or "-",
            short(st["recorded"]), lag, note,
        ])
    hint = "" if args.fetch else "\n(lag uses local remote refs; add --fetch for current numbers)"
    emit(args, {"root": str(root), "cli_version": __version__, "submodules": states}, table(rows) + hint)
    return 0


# ---------------------------------------------------------------- init

def cmd_init(root: Path, subs: list[Sub], args) -> int:
    chosen = select(subs, args, lambda s: args.all or s.eff_policy != "lazy")
    results = []
    for s in chosen:
        if is_initialized(root, s):
            results.append({"name": s.name, "action": "skipped",
                            "reason": "already initialized; init never moves a checkout (use pull/bump)"})
            continue
        cmd = ["submodule", "update", "--init"]
        if s.eff_policy == "lazy" or s.update == "none":
            cmd.append("--checkout")  # override update=none for an explicit request
        if args.recursive:
            cmd.append("--recursive")
        cmd += ["--", s.path]
        if not args.dry_run:
            git("submodule", "sync", "--", s.path, cwd=root)
            git(*cmd, cwd=root)
        results.append({"name": s.name, "action": "would-init" if args.dry_run else "initialized",
                        "command": "git " + " ".join(cmd)})
    text = "\n".join(f"{r['action']:12} {r['name']}" + (f"  ({r['reason']})" if "reason" in r else "")
                     for r in results) or "nothing selected"
    emit(args, {"results": results}, text)
    return 0


# ---------------------------------------------------------------- pull

def pull_one(root: Path, s: Sub, args) -> dict:
    p = root / s.path
    branch = s.eff_branch(root)
    up = f"origin/{branch}"
    res = {"name": s.name, "branch": branch}
    if s.eff_policy != "track" and not args.force:
        raise Refused(f"policy is {s.policy or 'unset (treated as pin)'}; pass --force to move it")
    if not is_initialized(root, s):
        raise Refused("not initialized; run `init` first")
    if not args.no_fetch and (err := fetch(p)):
        raise Refused(f"fetch failed: {err}")
    if not ref_exists(p, f"refs/remotes/{up}"):
        raise Refused(f"{up} does not exist")
    if tracked_dirty(p):
        raise Refused("uncommitted changes in the checkout")
    cur = git("symbolic-ref", "-q", "--short", "HEAD", cwd=p, check=False)
    head = git("rev-parse", "HEAD", cwd=p)
    if cur and cur != branch:
        raise Refused(f"checkout is on branch {cur!r}; develop in `worktree add`, keep the checkout on {branch}")
    if not cur and not is_ancestor(p, head, up):
        raise Refused(f"detached commit {short(head)} is not on {up}; save it on a branch first")
    if ref_exists(p, f"refs/heads/{branch}"):
        local = git("rev-parse", branch, cwd=p)
        behind, ahead = is_ancestor(p, local, up), is_ancestor(p, up, local)
        if not behind and not ahead:
            raise Refused(f"local {branch} has diverged from {up}; resolve manually")
        if not behind:
            res["warning"] = f"local {branch} has unpushed commits; bump will refuse until pushed"
    target = git("rev-parse", up, cwd=p)
    res.update({"from": head, "to": target})
    if head == target and cur == branch:
        res["action"] = "up-to-date"
        return res
    if args.dry_run:
        res["action"] = "would-update"
        return res
    if not cur:
        if ref_exists(p, f"refs/heads/{branch}"):
            git("switch", branch, cwd=p)
        else:
            git("switch", "--track", "-c", branch, up, cwd=p)
    git("merge", "--ff-only", up, cwd=p)
    res["to"] = git("rev-parse", "HEAD", cwd=p)
    res["action"] = "updated"
    return res


def cmd_pull(root: Path, subs: list[Sub], args) -> int:
    chosen = select(subs, args, lambda s: s.eff_policy == "track" and is_initialized(root, s))
    results, failed = [], False
    for s in chosen:
        try:
            results.append(pull_one(root, s, args))
        except Refused as e:
            failed = True
            results.append({"name": s.name, "action": "refused", "reason": str(e)})
    lines = []
    for r in results:
        detail = r.get("reason") or f"{short(r.get('from'))} -> {short(r.get('to'))}"
        lines.append(f"{r['action']:12} {r['name']}  {detail}" + (f"  [{r['warning']}]" if r.get("warning") else ""))
    if any(r["action"] == "updated" for r in results):
        lines.append("checkouts moved; record them with `bump` (gitlinks are unchanged until then)")
    emit(args, {"results": results}, "\n".join(lines) or "nothing selected")
    return 1 if failed else 0


# ---------------------------------------------------------------- preflight / bump

def check_commit(root: Path, s: Sub, sha: str, *, require_clean: bool) -> list[str]:
    """Problems that make `sha` unsafe to record as this submodule's gitlink."""
    p = root / s.path
    branch = s.eff_branch(root)
    if not is_initialized(root, s):
        return ["not initialized; cannot verify the commit"]
    problems = []
    if require_clean and tracked_dirty(p):
        problems.append("uncommitted changes in the checkout")
    if not has_commit(p, sha):
        return problems + [f"{short(sha)} does not exist in the child repo"]
    if s.eff_policy != "track":
        # A pin may sit on any pushed branch (e.g. a production baseline); it must only be recoverable.
        if not remote_refs_containing(p, sha):
            problems.append(f"{short(sha)} is not reachable from any origin branch; push the child commit (then fetch)")
        return problems
    if not ref_exists(p, f"refs/remotes/origin/{branch}"):
        return problems + [f"origin/{branch} missing; cannot prove {short(sha)} is pushed"]
    if not is_ancestor(p, sha, f"origin/{branch}"):
        problems.append(f"{short(sha)} is not reachable from origin/{branch}; push the child commit (then fetch)")
    return problems


def cmd_preflight(root: Path, subs: list[Sub], args) -> int:
    by_path = {s.path: s for s in subs}
    findings = []
    if git("ls-files", "-u", cwd=root):
        for line in git("ls-files", "-u", cwd=root).splitlines():
            if line.startswith("160000"):
                findings.append({"path": line.split("\t", 1)[1], "level": "error", "message": "unmerged gitlink"})
    raw = git("diff", "--cached", "--raw", "--no-abbrev", cwd=root)
    staged = []
    for line in raw.splitlines():
        m = re.match(r":\d+ (\d+) [0-9a-f]+ ([0-9a-f]+) \w+\t(.+)", line)
        if m and m.group(1) == "160000":
            staged.append((m.group(3), m.group(2)))
    for path, sha in staged:
        s = by_path.get(path)
        if not s:
            findings.append({"path": path, "level": "error", "message": "gitlink not declared in .gitmodules"})
            continue
        if args.fetch and is_initialized(root, s):
            fetch(root / s.path)
        for msg in check_commit(root, s, sha, require_clean=False):
            findings.append({"path": path, "level": "error", "message": msg})
        if is_initialized(root, s):
            p = root / s.path
            if tracked_dirty(p):
                findings.append({"path": path, "level": "warn", "message": "checkout has uncommitted changes"})
            if git("rev-parse", "HEAD", cwd=p, check=False) != sha:
                findings.append({"path": path, "level": "warn", "message": "checkout HEAD differs from the staged gitlink"})
    errors = [f for f in findings if f["level"] == "error"]
    text = "\n".join(f"{f['level']:5} {f['path']}: {f['message']}" for f in findings)
    if not staged:
        text = text or "No staged gitlink changes."
    elif not findings:
        text = f"ok: {len(staged)} staged gitlink(s) are pushed and reachable"
    emit(args, {"staged": [{"path": p, "sha": s} for p, s in staged], "findings": findings, "ok": not errors}, text)
    return 1 if errors else 0


def cmd_bump(root: Path, subs: list[Sub], args) -> int:
    if not args.names and not args.all_track:
        raise UsageError("name submodules to bump, or pass --all-track")
    chosen = select(subs, args, lambda s: args.all_track and s.eff_policy == "track" and is_initialized(root, s))
    planned, refused, results = [], [], []
    for s in chosen:
        p = root / s.path
        res = {"name": s.name, "path": s.path, "policy": s.policy}
        try:
            if s.eff_policy != "track" and not args.reason:
                raise Refused(f"policy is {s.policy or 'unset (treated as pin)'}; pass --reason to move it")
            if not is_initialized(root, s):
                raise Refused("not initialized")
            if not args.no_fetch and (err := fetch(p)):
                raise Refused(f"fetch failed: {err}")
            head = git("rev-parse", "HEAD", cwd=p)
            old = gitlink(root, s.path)
            res.update({"from": old, "to": head})
            if head == old and index_gitlink(root, s.path) == old:
                res["action"] = "up-to-date"
                results.append(res)
                continue
            if problems := check_commit(root, s, head, require_clean=True):
                raise Refused("; ".join(problems))
            if old and has_commit(p, old):
                res["commits"] = int(git("rev-list", "--count", f"{old}..{head}", cwd=p))
            res["action"] = "would-bump" if args.dry_run else "staged"
            planned.append((s, res))
        except Refused as e:
            res.update(action="refused", reason=str(e))
            refused.append(res)
        results.append(res)

    commit_sha = None
    if refused and not args.partial:
        for _, res in planned:
            res["action"] = "aborted"
    elif planned and not args.dry_run:
        paths = [s.path for s, _ in planned]
        if args.commit:
            others = set(git("diff", "--cached", "--name-only", cwd=root).splitlines()) - set(paths)
            if others and not args.allow_other_staged:
                raise Refused(f"other staged changes would join the bump commit: {', '.join(sorted(others))}")
        git("add", "--", *paths, cwd=root)
        if args.commit:
            git("commit", "-F", "-", cwd=root, input=bump_message(root, planned, args))
            commit_sha = git("rev-parse", "HEAD", cwd=root)
            for _, res in planned:
                res["action"] = "committed"

    lines = []
    for r in results:
        if r["action"] == "refused":
            lines.append(f"refused      {r['name']}  {r['reason']}")
        else:
            n = f" (+{r['commits']})" if r.get("commits") is not None else ""
            lines.append(f"{r['action']:12} {r['name']}  {short(r.get('from'))} -> {short(r.get('to'))}{n}")
    if refused and not args.partial:
        lines.append("aborted: one cross-repo change gets one outer commit; fix the refusals or pass --partial")
    if commit_sha:
        lines.append(f"committed {short(commit_sha)}")
    elif planned and not args.dry_run and not (refused and not args.partial):
        lines.append("gitlinks staged; review with `git diff --cached --submodule=log`, then commit (or rerun with --commit)")
    emit(args, {"results": results, "commit": commit_sha}, "\n".join(lines) or "nothing selected")
    return 1 if refused else 0


def bump_message(root: Path, planned: list[tuple[Sub, dict]], args) -> str:
    names = [s.name for s, _ in planned]
    subject = args.subject or (
        f"chore(submodules): bump {', '.join(names)}" if len(names) <= 3
        else f"chore(submodules): bump {len(names)} submodules"
    )
    body = []
    for s, r in planned:
        n = f" (+{r['commits']})" if r.get("commits") is not None else ""
        body.append(f"- {s.name}: {short(r['from'])}..{short(r['to'])}{n} [{s.policy or 'unset'}]")
    if args.reason:
        body += ["", f"Reason: {args.reason}"]
    log = git("diff", "--cached", "--submodule=log", "--", *[s.path for s, _ in planned], cwd=root)
    if log:
        body += ["", log]
    return subject + "\n\n" + "\n".join(body) + "\n"


# ---------------------------------------------------------------- worktrees

def wt_path(root: Path, s: Sub, branch: str) -> Path:
    return root / WORKTREE_DIR / s.path / branch.replace("/", "-")


def ensure_gitignore(root: Path, dry_run: bool) -> bool:
    """Return True when .gitignore needs (or got) the .worktrees/ entry."""
    if git_rc("check-ignore", "-q", "--no-index", f"{WORKTREE_DIR}/probe", cwd=root) == 0:
        return False
    if not dry_run:
        gi = root / ".gitignore"
        text = gi.read_text() if gi.exists() else ""
        sep = "" if not text or text.endswith("\n") else "\n"
        gi.write_text(f"{text}{sep}# superproject-workspace: child worktrees\n{WORKTREE_DIR}/\n")
    return True


def cmd_worktree(root: Path, subs: list[Sub], args) -> int:
    if args.wt_cmd == "list":
        chosen = [s for s in subs if is_initialized(root, s)]
        items = [dict(wt, submodule=s.name) for s in chosen for wt in list_child_worktrees(root, s)]
        rows = [["SUBMODULE", "BRANCH", "PATH", "STATE"]]
        for wt in items:
            state = ["prunable"] if wt["prunable"] else []
            if wt.get("dirty"):
                state.append(f"dirty({wt['dirty']})")
            if wt["merged"]:
                state.append("merged: safe to remove")
            rows.append([wt["submodule"], wt["branch"] or "(detached)", wt["path"], ", ".join(state)])
        emit(args, {"worktrees": items}, table(rows) if items else "no child worktrees")
        return 0

    s = resolve(subs, args.submodule)
    p = root / s.path
    if not is_initialized(root, s):
        raise Refused(f"{s.name} is not initialized; run `init {s.name}` first")
    target = wt_path(root, s, args.branch)
    rel = str(target.relative_to(root))

    if args.wt_cmd == "remove":
        cmd = ["worktree", "remove", *(["--force"] if args.force else []), str(target)]
        if not args.dry_run:
            git(*cmd, cwd=p)
            git("worktree", "prune", cwd=p)
            if args.delete_branch:
                git("branch", "-D" if args.force else "-d", args.branch, cwd=p)
        emit(args, {"removed": rel, "dry_run": args.dry_run}, f"{'would remove' if args.dry_run else 'removed'} {rel}")
        return 0

    # add
    if target.exists():
        raise Refused(f"{rel} already exists")
    if not args.no_fetch:
        fetch(p)
    branch = s.eff_branch(root)
    if ref_exists(p, f"refs/heads/{args.branch}"):
        cmd, base = ["worktree", "add", str(target), args.branch], args.branch
    elif ref_exists(p, f"refs/remotes/origin/{args.branch}"):
        base = f"origin/{args.branch}"
        cmd = ["worktree", "add", "--track", "-b", args.branch, str(target), base]
    else:
        # Pinned children branch from the recorded baseline, not from upstream tip.
        base = args.base or (f"origin/{branch}" if s.eff_policy == "track" else gitlink(root, s.path))
        cmd = ["worktree", "add", "-b", args.branch, str(target), base]
    gi = ensure_gitignore(root, args.dry_run)
    if not args.dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        git(*cmd, cwd=p)
    data = {"path": rel, "branch": args.branch, "base": base, "gitignore_updated": gi, "dry_run": args.dry_run}
    emit(args, data, f"{'would create' if args.dry_run else 'created'} {rel} on {args.branch} from {base}"
         + ("\nadded .worktrees/ to .gitignore" if gi else ""))
    return 0


# ---------------------------------------------------------------- audit

def find_agents_file(root: Path) -> Path | None:
    for name in ("AGENTS.md", "CLAUDE.md"):
        if (root / name).exists():
            return root / name
    return None


def find_justfile(root: Path) -> Path | None:
    for name in ("justfile", "Justfile", ".justfile"):
        if (root / name).exists():
            return root / name
    return None


def cmd_audit(root: Path, subs: list[Sub], args) -> int:
    f: list[dict] = []

    def add(level: str, code: str, subject: str, message: str, fix: str = "") -> None:
        f.append({"level": level, "code": code, "subject": subject, "message": message, "fix": fix})

    if not subs:
        add("error", "no-submodules", ".gitmodules", "no submodules declared")
    for s in subs:
        if s.policy is None:
            add("warn", "policy-missing", s.name, "no x-policy; treated as pin",
                f"git config -f .gitmodules submodule.{s.name}.x-policy track|pin|lazy")
        elif s.policy not in POLICIES:
            add("error", "policy-invalid", s.name, f"x-policy={s.policy!r} (expected {'|'.join(POLICIES)})")
        if s.bump and s.bump not in BUMP_MODES:
            add("error", "bump-invalid", s.name, f"x-bump={s.bump!r} (expected {'|'.join(BUMP_MODES)})")
        if s.bump in ("pr", "direct") and s.eff_policy != "track":
            add("warn", "bump-ignored", s.name, f"x-bump={s.bump} has no effect on a {s.eff_policy} submodule")
        if s.eff_policy == "track" and not s.branch:
            add("warn", "branch-missing", s.name, "track without `branch`; assuming main",
                f"git config -f .gitmodules submodule.{s.name}.branch main")
        if s.policy == "lazy" and s.update != "none":
            add("warn", "lazy-update", s.name, "lazy without `update = none`; plain `git submodule update --init` will fetch it",
                f"git config -f .gitmodules submodule.{s.name}.update none")
        if s.policy in ("track", "pin") and s.update == "none":
            add("warn", "update-none", s.name, f"{s.policy} child has update=none; plain git will never check it out")
        st = sub_state(root, s, do_fetch=args.fetch)
        if not st["initialized"]:
            if s.eff_policy != "lazy":
                add("warn", "uninitialized", s.name, f"{s.eff_policy} child is not initialized", f"init {s.name}")
            continue
        configured = git("config", "--get", f"submodule.{s.name}.url", cwd=root, check=False)
        if s.url and configured and configured != s.url and not s.url.startswith("."):
            add("warn", "url-unsynced", s.name, f".git/config url differs from .gitmodules ({configured})",
                f"git submodule sync -- {s.path}")
        if st["recorded_on_remote"] is False:
            add("error", "gitlink-unreachable", s.name,
                f"recorded {short(st['recorded'])} is on no origin branch; a fresh clone cannot check it out",
                "push the child commit, or move the pointer to a pushed commit")
        elif st["recorded_reachable"] is False:
            add("warn" if s.eff_policy == "track" else "info", "gitlink-off-branch", s.name,
                f"recorded {short(st['recorded'])} is pushed but not on origin/{st['branch']}",
                "merge the child branch, or set `branch` to the baseline it follows")
        if st["drift"]:
            add("info", "checkout-drift", s.name, f"checkout at {short(st['head'])}, gitlink at {short(st['recorded'])}",
                f"bump {s.name} to record it, or `git submodule update -- {s.path}` to discard")
        if st["dirty"]:
            add("info", "dirty", s.name, f"{st['dirty']} uncommitted change(s) in the checkout")
        if s.eff_policy == "track" and st["lag"]:
            add("warn", "behind", s.name, f"gitlink is {st['lag']} commit(s) behind origin/{st['branch']}",
                f"pull {s.name} && bump {s.name}")
        if s.eff_policy == "pin" and st["lag"]:
            add("info", "pin-behind", s.name, f"pinned {st['lag']} commit(s) behind origin/{st['branch']}")
        for w in st["worktrees"]:
            if w["prunable"]:
                add("info", "worktree-prunable", s.name, f"{w['path']} is gone", f"git -C {s.path} worktree prune")
            elif w["merged"]:
                add("info", "worktree-merged", s.name, f"{w['path']} ({w['branch']}) is merged",
                    f"worktree remove {s.name} {w['branch']} --delete-branch")
        for w in st["warnings"]:
            add("warn", "state", s.name, w)

    agents = find_agents_file(root)
    if not agents or AGENTS_BEGIN not in agents.read_text():
        add("warn", "agents-block", agents.name if agents else "AGENTS.md",
            "no superproject-workspace guidance block for agents", "adopt")
    if git_rc("check-ignore", "-q", "--no-index", f"{WORKTREE_DIR}/probe", cwd=root) != 0:
        add("warn", "worktrees-not-ignored", ".gitignore", f"{WORKTREE_DIR}/ is not ignored", "adopt")
    jf = find_justfile(root)
    if jf:
        text = jf.read_text()
        hard = [s.path for s in subs if s.path in text]
        if JUST_BEGIN not in text and len(hard) >= 2:
            add("info", "justfile-hardcoded", jf.name,
                f"recipes hard-code {len(hard)} submodule paths; policy-driven recipes avoid per-child edits", "adopt")
    # The tool itself drifts too: compare managed blocks and any vendored copy to this CLI.
    if SKILL_ASSETS.exists():
        for target, begin, end, asset in (
            (agents, AGENTS_BEGIN, AGENTS_END, "agents-block.md.template"),
            (jf, JUST_BEGIN, JUST_END, "justfile.snippet"),
        ):
            block = extract_block(target.read_text(), begin, end) if target else None
            want = extract_block(render_asset(asset), begin, end)
            if block and want and block != want:
                add("warn", "managed-block-stale", target.name,
                    f"managed block differs from superproject-workspace {__version__}", "adopt")
    vendored = root / VENDORED_CLI
    if vendored.exists() and vendored.resolve() != Path(__file__).resolve() \
            and vendored.read_bytes() != Path(__file__).read_bytes():
        add("warn", "vendored-cli-stale", VENDORED_CLI,
            f"vendored CLI {cli_version(vendored)} differs from running CLI {__version__}",
            "adopt --vendor-cli to refresh, or delete it to use the installed skill")
    automated = [s for s in subs if s.eff_bump in ("pr", "direct")]
    wf_dir = root / ".github" / "workflows"
    has_ci = wf_dir.is_dir() and any("ci-plan" in w.read_text() or "superproject.py" in w.read_text()
                                      for w in wf_dir.glob("*.y*ml"))
    if automated and not has_ci:
        add("warn", "ci-missing", ".github/workflows",
            f"{len(automated)} child(ren) want automated bumps but no bump workflow exists", "adopt --with-ci")
    if git("config", "--get", "push.recurseSubmodules", cwd=root, check=False) not in ("check", "on-demand"):
        add("info", "push-check", "git config", "push.recurseSubmodules is not set; outer pushes can reference unpushed children",
            "git config push.recurseSubmodules check")

    counts = {lvl: sum(1 for x in f if x["level"] == lvl) for lvl in ("error", "warn", "info")}
    order = {"error": 0, "warn": 1, "info": 2}
    lines = [f"{x['level']:5} {x['code']:22} {x['subject']}: {x['message']}" + (f"\n      fix: {x['fix']}" if x["fix"] else "")
             for x in sorted(f, key=lambda x: order[x["level"]])]
    lines.append(f"\n{counts['error']} error(s), {counts['warn']} warning(s), {counts['info']} info")
    emit(args, {"findings": f, "counts": counts}, "\n".join(lines))
    failed = counts["error"] or (args.strict and counts["warn"])
    return 1 if failed else 0


# ---------------------------------------------------------------- adopt

def render_asset(name: str) -> str:
    path = SKILL_ASSETS / name
    if not path.exists():
        raise UsageError(f"asset {name} not found; run adopt from the installed skill, not a vendored copy")
    return path.read_text()


def extract_block(text: str, begin: str, end: str) -> str | None:
    m = re.search(re.escape(begin) + r".*?" + re.escape(end), text, re.S)
    return m.group(0) if m else None


def cli_version(path: Path) -> str:
    m = re.search(r'^__version__ = "([^"]+)"', path.read_text(), re.M)
    return m.group(1) if m else "?"


def upsert_block(text: str, begin: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block.strip("\n"), text, count=1)
    sep = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
    return f"{text}{sep}\n{block.strip(chr(10))}\n" if text else block.strip("\n") + "\n"


def cmd_adopt(root: Path, subs: list[Sub], args) -> int:
    actions: list[dict] = []
    overrides: dict[str, tuple[str, str | None]] = {}
    for spec in args.set or []:
        ident, _, val = spec.partition("=")
        pol, _, bump = val.partition(":")
        if pol not in POLICIES or (bump and bump not in BUMP_MODES):
            raise UsageError(f"--set {spec!r}: expected NAME=track|pin|lazy[:pr|direct|manual]")
        overrides[resolve(subs, ident).name] = (pol, bump or None)

    def set_key(s: Sub, key: str, value: str) -> None:
        actions.append({"kind": "gitmodules", "target": f"submodule.{s.name}.{key}", "detail": value})
        if not args.dry_run:
            git("config", "-f", ".gitmodules", f"submodule.{s.name}.{key}", value, cwd=root)

    for s in subs:
        forced = overrides.get(s.name)
        policy = forced[0] if forced else (s.policy or args.policy_default)
        if policy != s.policy:
            set_key(s, "x-policy", policy)
        if policy == "track":
            bump = (forced and forced[1]) or s.bump or args.bump_default
            if bump != s.bump:
                set_key(s, "x-bump", bump)
        if not s.branch and policy != "lazy":
            remote_head = ""
            if is_initialized(root, s):
                remote_head = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD",
                                  cwd=root / s.path, check=False).removeprefix("origin/")
            set_key(s, "branch", remote_head or "main")
        if policy == "lazy" and s.update != "none":
            set_key(s, "update", "none")

    if args.vendor_cli:
        # Opt-in only (offline / air-gapped): a copy stops receiving skill updates.
        dest = root / VENDORED_CLI
        src = Path(__file__).resolve()
        if dest.resolve() != src and (not dest.exists() or dest.read_bytes() != src.read_bytes()):
            actions.append({"kind": "file", "target": VENDORED_CLI,
                            "detail": f"{'refresh' if dest.exists() else 'vendor'} CLI {__version__}"})
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

    if not args.no_agents:
        agents = find_agents_file(root) or root / "AGENTS.md"
        old = agents.read_text() if agents.exists() else ""
        new = upsert_block(old, AGENTS_BEGIN, AGENTS_END, render_asset("agents-block.md.template"))
        if new != old:
            actions.append({"kind": "file", "target": agents.name, "detail": "upsert agent guidance block"})
            if not args.dry_run:
                agents.write_text(new)

    if not args.no_justfile:
        jf = find_justfile(root) or root / "justfile"
        old = jf.read_text() if jf.exists() else ""
        new = upsert_block(old, JUST_BEGIN, JUST_END, render_asset("justfile.snippet"))
        if new != old:
            actions.append({"kind": "file", "target": jf.name, "detail": "upsert sub-* recipes"})
            if not args.dry_run:
                jf.write_text(new)

    if not args.no_gitignore and ensure_gitignore(root, args.dry_run):
        actions.append({"kind": "file", "target": ".gitignore", "detail": f"ignore {WORKTREE_DIR}/"})

    if args.with_ci:
        wf = root / ".github" / "workflows" / "superproject-bump.yml"
        content = render_asset("superproject-bump.yml")
        if not wf.exists() or wf.read_text() != content:
            actions.append({"kind": "file", "target": str(wf.relative_to(root)), "detail": "scheduled bump workflow"})
            if not args.dry_run:
                wf.parent.mkdir(parents=True, exist_ok=True)
                wf.write_text(content)

    if args.with_hook:
        hook = root / git("rev-parse", "--git-path", "hooks/pre-commit", cwd=root)
        if hook.exists():
            if render_asset("pre-commit-hook.sh") != hook.read_text():
                actions.append({"kind": "skipped", "target": "pre-commit hook",
                                "detail": "a different hook exists; chain `preflight` into it by hand"})
        else:
            actions.append({"kind": "file", "target": "pre-commit hook", "detail": "run preflight before commits"})
            if not args.dry_run:
                hook.parent.mkdir(parents=True, exist_ok=True)
                hook.write_text(render_asset("pre-commit-hook.sh"))
                hook.chmod(0o755)

    if not args.no_git_config:
        for key, value in (("diff.submodule", "log"), ("status.submoduleSummary", "true"),
                           ("push.recurseSubmodules", "check")):
            if not git("config", "--local", "--get", key, cwd=root, check=False):
                actions.append({"kind": "git-config", "target": key, "detail": value})
                if not args.dry_run:
                    git("config", "--local", key, value, cwd=root)

    verb = "would" if args.dry_run else "did"
    text = "\n".join(f"{verb}: {a['kind']:10} {a['target']} = {a['detail']}" for a in actions) or "already adopted; nothing to do"
    if actions and not args.dry_run:
        text += "\nreview with `git diff`, then run `audit`"
    emit(args, {"actions": actions, "dry_run": args.dry_run}, text)
    return 0


# ---------------------------------------------------------------- ci-plan

def cmd_ci_plan(root: Path, subs: list[Sub], args) -> int:
    chosen = [s for s in subs if s.eff_bump in ("pr", "direct")]
    if args.only:
        chosen = [s for s in chosen if s.name == args.only or s.path == args.only]
    plan = {mode: [{"name": s.name, "path": s.path, "branch": s.eff_branch(root)}
                   for s in chosen if s.eff_bump == mode] for mode in ("pr", "direct")}
    plan["init_paths"] = [s.path for s in chosen]
    text = "\n".join(f"{mode}: {', '.join(x['name'] for x in plan[mode]) or '-'}" for mode in ("pr", "direct"))
    emit(args, plan, text)
    return 0


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="superproject root (default: discovered from cwd)")
    common.add_argument("--json", action="store_true", help="machine-readable output on stdout")

    sel = argparse.ArgumentParser(add_help=False)
    sel.add_argument("names", nargs="*", help="submodule name, path, or basename")
    sel.add_argument("--tier", help="only submodules with this x-tier")
    sel.add_argument("--policy", choices=POLICIES, help="only submodules with this effective policy")

    dry = argparse.ArgumentParser(add_help=False)
    dry.add_argument("--dry-run", action="store_true", help="report what would change; change nothing")

    ap = argparse.ArgumentParser(
        prog="superproject.py",
        description="Keep a git-submodule superproject on track (policy-driven status, bump, worktrees, audit).",
        epilog="Policy lives in .gitmodules: x-policy=track|pin|lazy, x-bump=pr|direct|manual, x-tier=<group>.",
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("status", parents=[common, sel], help="policy, lag and drift for every child")
    p.add_argument("--fetch", action="store_true", help="fetch each child's origin first")
    p.set_defaults(func=cmd_status)

    p = sp.add_parser("init", parents=[common, sel, dry],
                      help="initialize children (lazy ones only when named, by --tier, or with --all)")
    p.add_argument("--all", action="store_true", help="include lazy children")
    p.add_argument("--recursive", action="store_true", help="also initialize nested submodules")
    p.set_defaults(func=cmd_init)

    p = sp.add_parser("pull", parents=[common, sel, dry],
                      help="fast-forward track children to origin/<branch> (checkout only; gitlink unchanged)")
    p.add_argument("--mode", choices=BUMP_MODES, help="only children with this effective x-bump")
    p.add_argument("--force", action="store_true", help="allow moving pin/lazy/unset children")
    p.add_argument("--no-fetch", action="store_true")
    p.set_defaults(func=cmd_pull)

    p = sp.add_parser("bump", parents=[common, sel, dry],
                      help="record children's current HEADs as gitlinks after preflight")
    p.add_argument("--all-track", action="store_true", help="every initialized track child")
    p.add_argument("--mode", choices=BUMP_MODES, help="only children with this effective x-bump")
    p.add_argument("--reason", help="required to move pin/lazy/unset children; goes into the commit body")
    p.add_argument("--commit", action="store_true", help="create one outer commit for all staged gitlinks")
    p.add_argument("--subject", help="override the commit subject")
    p.add_argument("--partial", action="store_true", help="bump the passing children even if others are refused")
    p.add_argument("--allow-other-staged", action="store_true", help="let unrelated staged changes join the commit")
    p.add_argument("--no-fetch", action="store_true")
    p.set_defaults(func=cmd_bump)

    p = sp.add_parser("preflight", parents=[common],
                      help="verify staged gitlinks are pushed and reachable (pre-commit hook)")
    p.add_argument("--fetch", action="store_true", help="fetch affected children first")
    p.set_defaults(func=cmd_preflight)

    p = sp.add_parser("worktree", parents=[common], help="child worktrees under .worktrees/<path>/<branch>")
    wsp = p.add_subparsers(dest="wt_cmd", required=True)
    w = wsp.add_parser("add", parents=[common, dry], help="create a child worktree on a branch")
    w.add_argument("submodule")
    w.add_argument("branch")
    w.add_argument("--base", help="start point for a new branch (default: origin/<branch> for track, gitlink otherwise)")
    w.add_argument("--no-fetch", action="store_true")
    w = wsp.add_parser("list", parents=[common], help="list child worktrees and whether they are merged")
    w = wsp.add_parser("remove", parents=[common, dry], help="remove a child worktree")
    w.add_argument("submodule")
    w.add_argument("branch")
    w.add_argument("--delete-branch", action="store_true", help="also delete the branch (safe delete unless --force)")
    w.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_worktree)

    p = sp.add_parser("audit", parents=[common], help="read-only health report with fixes")
    p.add_argument("--fetch", action="store_true")
    p.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    p.set_defaults(func=cmd_audit)

    p = sp.add_parser("adopt", parents=[common, dry], help="write policy keys, agent guidance, recipes, and optional CI")
    p.add_argument("--policy-default", choices=POLICIES, default="pin",
                   help="policy for children that declare none (default: pin)")
    p.add_argument("--bump-default", choices=BUMP_MODES, default="manual",
                   help="x-bump for track children that declare none (default: manual)")
    p.add_argument("--set", action="append", metavar="NAME=POLICY[:BUMP]", help="explicit per-child policy (repeatable)")
    p.add_argument("--vendor-cli", action="store_true",
                   help=f"copy this CLI to {VENDORED_CLI} (offline use only; the copy stops receiving skill updates)")
    p.add_argument("--no-agents", action="store_true")
    p.add_argument("--no-justfile", action="store_true")
    p.add_argument("--no-gitignore", action="store_true")
    p.add_argument("--no-git-config", action="store_true",
                   help="skip local diff.submodule/status.submoduleSummary/push.recurseSubmodules")
    p.add_argument("--with-ci", action="store_true", help="add .github/workflows/superproject-bump.yml")
    p.add_argument("--with-hook", action="store_true", help="install a pre-commit hook running preflight")
    p.set_defaults(func=cmd_adopt)

    p = sp.add_parser("ci-plan", parents=[common], help="children the bump workflow should handle, grouped by mode")
    p.add_argument("--only", help="restrict to one child (repository_dispatch)")
    p.set_defaults(func=cmd_ci_plan)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = find_root(args.root)
        return args.func(root, load_subs(root), args)
    except UsageError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
