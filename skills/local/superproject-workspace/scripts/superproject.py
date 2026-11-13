#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Keep a multi-repo workspace on track: a submodule superproject or a pointer-only home repo.

A gitlink records a commit, not a branch, so a superproject drifts by design.
This CLI makes the drift visible and moves pointers according to a
per-submodule policy stored as extra keys in `.gitmodules`:

    [submodule "app"]
        path = app
        url = https://example.com/org/app.git
        branch = main        # tracking branch (native git key)
        x-policy = track     # track | pin | lazy
        x-bump = pr          # pr | direct | manual   (only meaningful for track)
        x-tier = core        # free-form grouping
        update = none        # set for lazy children (native git key)
        x-role = Web client  # one-line purpose (optional)

A workspace root is a directory holding `.gitmodules` or a `.superproject`
marker (git-config syntax; `new` creates it) with workspace settings:

    [workspace]
        mode = submodule            # default kind for `add`: submodule | pointer
        worktree-root = .worktrees  # relative to the root, absolute, or ~
        map-file = docs/repos.md    # optional: full repo map lives here
    [repo "docs-site"]              # a pointer child: plain clone, no gitlink
        path = repos/docs-site
        url = https://example.com/org/docs-site.git
        branch = main
        x-tier = reference
        x-role = Public documentation site

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

__version__ = "0.3.0"

POLICIES = ("track", "pin", "lazy")
BUMP_MODES = ("pr", "direct", "manual")
WORKTREE_DIR = ".worktrees"  # default worktree root, relative to the workspace root
MARKER = ".superproject"
TASKS_DIR = "_tasks"  # reserved first path segment under the worktree root
# submodule: declared in .gitmodules, pinned by a gitlink.
# pointer: declared as `[repo "<name>"]` in .superproject; a plain clone, no gitlink.
KINDS = ("submodule", "pointer")
MODES = KINDS
MAP_BEGIN = "<!-- superproject-workspace:repo-map -->"
MAP_END = "<!-- /superproject-workspace:repo-map -->"
MAP_INLINE_MAX = 25
REPAIR_DOC = "references/repair.md in the superproject-workspace skill"

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
    if not Path(cwd).is_dir():
        if check:
            raise Refused(f"git {' '.join(args)}: {cwd} does not exist")
        return ""
    p = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, env=GIT_ENV, input=input
    )
    if check and p.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed in {cwd}: {p.stderr.strip()}")
    return p.stdout.rstrip("\n")


def git_rc(*args: str, cwd: Path) -> int:
    if not Path(cwd).is_dir():
        return 128
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


def git_dirs(repo: Path) -> tuple[Path, Path] | None:
    """(git_dir, common_dir) of the repository at `repo`, or None outside a repository.

    They differ in a linked worktree. `--path-format` is avoided on purpose
    (older git); a relative common dir is relative to `repo`.
    """
    out = git("rev-parse", "--absolute-git-dir", "--git-common-dir", cwd=repo, check=False).splitlines()
    if len(out) != 2:
        return None
    gd, cd = Path(out[0]), Path(out[1])
    return gd.resolve(), (cd if cd.is_absolute() else repo / cd).resolve()


def display_path(root: Path, p: Path) -> str:
    """Path relative to the root when inside it, else absolute."""
    p = p.resolve()
    try:
        return str(p.relative_to(root.resolve()))
    except ValueError:
        return str(p)


def marker_get(root: Path, key: str) -> str | None:
    if not (root / MARKER).exists():
        return None
    return git("config", "-f", MARKER, "--get", key, cwd=root, check=False) or None


def is_workspace_root(d: Path) -> bool:
    return (d / ".gitmodules").exists() or (d / MARKER).exists()


def worktree_root(root: Path) -> Path:
    """Where child worktrees live.

    Precedence: `git config --local superproject.worktreeRoot` (per clone) >
    `.superproject` workspace.worktree-root (tracked) > `.worktrees`.
    """
    val = (git("config", "--local", "--get", "superproject.worktreeRoot", cwd=root, check=False)
           or marker_get(root, "workspace.worktree-root") or WORKTREE_DIR)
    p = Path(val).expanduser()
    return p if p.is_absolute() else root / p


def worktree_root_rel(root: Path, wt_root: Path | None = None) -> str | None:
    """The worktree root relative to the workspace root (posix), or None when outside it."""
    try:
        return (wt_root or worktree_root(root)).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


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
    kind: str = "submodule"  # submodule (.gitmodules) | pointer (.superproject [repo])
    role: str | None = None  # x-role: one-line purpose

    @property
    def eff_policy(self) -> str:
        if self.kind == "pointer":
            return "pointer"
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
        head = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", cwd=child_dir(root, self), check=False)
        return head.removeprefix("origin/") if head.startswith("origin/") else "main"


def child_dir(root: Path, s: Sub) -> Path:
    """The child's checkout: `~` expanded, relative paths resolved against the root."""
    p = Path(s.path).expanduser()
    return p if p.is_absolute() else root / p


def wt_key(s: Sub) -> str:
    """The child's directory key under the worktree root."""
    return s.path if s.kind == "submodule" else s.name


def root_from_common_dir(common: Path) -> Path | None:
    """Workspace root owning a submodule git store, derived from its common dir.

    `<X>/.git/modules/...` belongs to the checkout at X. A store under
    `<X>/.git/worktrees/<id>/modules/...` belongs to the linked worktree
    recorded in `<X>/.git/worktrees/<id>/gitdir`. This finds the root from a
    child worktree that lives outside the workspace root. For nested
    submodules it yields the outermost root.
    """
    parts = common.parts
    for i in range(len(parts) - 1):
        if parts[i] != ".git":
            continue
        if parts[i + 1] == "modules":
            cand = Path(*parts[:i])
        elif parts[i + 1] == "worktrees" and len(parts) > i + 3 and parts[i + 3] == "modules":
            gitdir_file = Path(*parts[:i + 3]) / "gitdir"
            if not gitdir_file.is_file():
                return None
            cand = Path(gitdir_file.read_text().strip()).parent
        else:
            continue
        return cand.resolve() if is_workspace_root(cand) else None
    return None


def find_root(explicit: str | None) -> Path:
    for source, value in (("--root", explicit), ("$SUPERPROJECT_ROOT", os.environ.get("SUPERPROJECT_ROOT"))):
        if value:
            root = Path(value).expanduser().resolve()
            if not is_workspace_root(root):
                raise UsageError(f"{source} {root} has no .gitmodules or {MARKER}; "
                                 "create a workspace with `new`, or point at an existing one")
            return root
    cwd = Path.cwd()
    for cand in (
        git("rev-parse", "--show-superproject-working-tree", cwd=cwd, check=False),
        git("rev-parse", "--show-toplevel", cwd=cwd, check=False),
    ):
        if cand and is_workspace_root(Path(cand)):
            return Path(cand).resolve()
    # A child worktree outside the root still knows its store's location.
    dirs = git_dirs(cwd)
    if dirs and (found := root_from_common_dir(dirs[1])):
        return found
    # Inside a child worktree under .worktrees/: walk up to the superproject.
    for base in [cwd, *cwd.parents]:
        if is_workspace_root(base) and (base / ".git").exists():
            return base.resolve()
    raise UsageError(f"not inside a workspace (no .gitmodules or {MARKER} found); "
                     "pass --root, set $SUPERPROJECT_ROOT, or create one with `new`")


def _load_cfg(root: Path, file: str, section: str) -> dict[str, dict[str, str]]:
    """{name: {key: value}} for every `[section "name"]` in a git-config file."""
    if not (root / file).exists():
        return {}
    out = subprocess.run(
        ["git", "config", "-z", "-f", file, "--get-regexp", rf"^{re.escape(section)}\."],
        cwd=root, capture_output=True, text=True, env=GIT_ENV,
    ).stdout
    entries: dict[str, dict[str, str]] = {}
    for rec in out.split("\0"):
        if not rec:
            continue
        key, _, value = rec.partition("\n")
        name, _, var = key[len(section) + 1:].rpartition(".")
        if name:
            entries.setdefault(name, {})[var.lower()] = value
    return entries


def load_subs(root: Path) -> list[Sub]:
    subs = [
        Sub(
            name=name, path=e["path"].rstrip("/"), url=e.get("url"), branch=e.get("branch"),
            policy=e.get("x-policy"), bump=e.get("x-bump"), tier=e.get("x-tier"),
            update=e.get("update"), kind="submodule", role=e.get("x-role"),
        )
        for name, e in _load_cfg(root, ".gitmodules", "submodule").items()
        if "path" in e
    ]
    subs += [
        Sub(
            name=name, path=(e.get("path") or f"repos/{name}").rstrip("/"), url=e.get("url"),
            branch=e.get("branch"), policy=None, bump=None, tier=e.get("x-tier"), update=None,
            kind="pointer", role=e.get("x-role"),
        )
        for name, e in _load_cfg(root, MARKER, "repo").items()
    ]
    return subs


def gitlink(root: Path, path: str, tree: str = "HEAD") -> str | None:
    out = git("ls-tree", tree, "--", path, cwd=root, check=False)
    m = re.match(r"160000 commit ([0-9a-f]+)\t", out)
    return m.group(1) if m else None


def index_gitlink(root: Path, path: str) -> str | None:
    out = git("ls-files", "-s", "--", path, cwd=root, check=False)
    m = re.match(r"160000 ([0-9a-f]+) 0\t", out)
    return m.group(1) if m else None


CHECKOUT_STATES = ("ok", "absent", "broken", "foreign")


def checkout_state(root: Path, sub: Sub) -> str:
    """ok | absent (missing or empty dir) | broken (.git that is not a working repo) | foreign (files, no .git).

    Derived from the checkout itself, not from `.git/config` or `git submodule
    status`, so a clone that lost its config entry still reads as ok.
    """
    p = child_dir(root, sub)
    if not os.path.lexists(p) or (p.is_dir() and not any(p.iterdir())):
        return "absent"
    if not p.is_dir():
        return "foreign"
    if not os.path.lexists(p / ".git"):
        return "foreign"
    top = git("rev-parse", "--show-toplevel", cwd=p, check=False)
    return "ok" if top and Path(top).resolve() == p.resolve() else "broken"


def is_initialized(root: Path, sub: Sub) -> bool:
    return checkout_state(root, sub) == "ok"


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
    elif any(getattr(args, k, None) for k in ("tier", "policy", "kind")):
        chosen = list(subs)
    else:
        chosen = [s for s in subs if default(s)]
    if getattr(args, "kind", None):
        chosen = [s for s in chosen if s.kind == args.kind]
    if getattr(args, "tier", None):
        chosen = [s for s in chosen if s.tier == args.tier]
    if getattr(args, "policy", None):
        chosen = [s for s in chosen if s.eff_policy == args.policy]
    if getattr(args, "mode", None):
        chosen = [s for s in chosen if s.eff_bump == args.mode]
    return chosen


def sub_state(root: Path, sub: Sub, *, do_fetch: bool = False) -> dict:
    p = child_dir(root, sub)
    branch = sub.eff_branch(root)
    state = checkout_state(root, sub)
    pointer = sub.kind == "pointer"
    st: dict = {
        "name": sub.name, "path": sub.path, "kind": sub.kind, "role": sub.role,
        "policy": "pointer" if pointer else sub.policy, "bump": sub.eff_bump,
        "tier": sub.tier, "branch": branch, "recorded": None if pointer else gitlink(root, sub.path),
        "staged": None, "initialized": state == "ok", "checkout": state, "warnings": [],
    }
    staged = None if pointer else index_gitlink(root, sub.path)
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
    if pointer:
        # No gitlink: lag is how far the clone's HEAD trails origin/<branch>.
        if head:
            ahead, behind = git("rev-list", "--left-right", "--count", f"{head}...{upstream}", cwd=p).split()
            st.update(lag=int(behind), unpushed=int(ahead), head_reachable=int(ahead) == 0)
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


def worktree_blocks(repo: Path) -> list[dict]:
    """Parsed `git worktree list --porcelain`. The first block is the main worktree
    (for a submodule git reports its store path there, not the checkout)."""
    out = git("worktree", "list", "--porcelain", cwd=repo, check=False)
    blocks = []
    for block in out.split("\n\n"):
        info: dict = {}
        for line in block.splitlines():
            k, _, v = line.partition(" ")
            info[k] = v or True
        if isinstance(info.get("worktree"), str):
            blocks.append(info)
    return blocks


def block_branch(info: dict) -> str | None:
    br = info.get("branch")
    return br.removeprefix("refs/heads/") if isinstance(br, str) else None


def classify_worktree(root: Path, path: Path, wt_root: Path | None = None) -> tuple[bool, str | None]:
    """(managed, task): managed when under the worktree root; task for `<R>/_tasks/<task>/...`."""
    base = (wt_root or worktree_root(root)).resolve()
    p = path.resolve()
    if not p.is_relative_to(base):
        return False, None
    parts = p.relative_to(base).parts
    return True, (parts[1] if len(parts) >= 3 and parts[0] == TASKS_DIR else None)


def count_untracked(repo: Path) -> int:
    out = git("status", "--porcelain", "--untracked-files=normal", cwd=repo, check=False)
    return sum(1 for line in out.splitlines() if line.startswith("??"))


def unpushed_count(repo: Path) -> int | None:
    """Commits on HEAD that no origin/* ref contains (independent of upstream config)."""
    out = git("rev-list", "--count", "HEAD", "--not", "--remotes=origin", cwd=repo, check=False)
    return int(out) if out.isdigit() else None


def list_child_worktrees(root: Path, sub: Sub, *, include_unmanaged: bool = False) -> list[dict]:
    """Linked worktrees of a child. Unmanaged ones (outside the worktree root) only on request."""
    p = child_dir(root, sub)
    base = worktree_root(root)
    found = []
    for info in worktree_blocks(p)[1:]:
        wt = Path(info["worktree"])
        managed, task = classify_worktree(root, wt, base)
        if not managed and not include_unmanaged:
            continue
        found.append({
            "path": display_path(root, wt), "abs_path": str(wt.resolve()),
            "branch": block_branch(info), "head": info.get("HEAD"),
            "prunable": "prunable" in info, "managed": managed, "task": task,
        })
    branch = sub.eff_branch(root)
    for wt in found:
        wt["merged"] = bool(
            wt["head"] and wt["branch"] != branch
            and is_ancestor(p, wt["head"], f"refs/remotes/origin/{branch}")
        )
        live = not wt["prunable"] and Path(wt["abs_path"]).is_dir()
        wt["dirty"] = tracked_dirty(Path(wt["abs_path"])) if live else None
        wt["untracked"] = count_untracked(Path(wt["abs_path"])) if live else None
        wt["unpushed"] = unpushed_count(Path(wt["abs_path"])) if live else None
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
        if st.get("checkout") == "broken":
            return "-", "BROKEN checkout (.git is not a working repository)"
        if st.get("checkout") == "foreign":
            return "-", "FOREIGN files at the path (no .git)"
        if st.get("kind") == "pointer":
            return "-", f"not cloned (clone on demand: init {st['name']})"
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
    # Pointer clones, like lazy children, happen only when named, by --tier/--kind, or with --all.
    chosen = select(subs, args, lambda s: args.all or s.eff_policy not in ("lazy", "pointer"))
    results, refused = [], False
    for s in chosen:
        state = checkout_state(root, s)
        if state == "ok":
            p = child_dir(root, s)
            head = git("rev-parse", "HEAD", cwd=p, check=False) or None
            recorded = None if s.kind == "pointer" else gitlink(root, s.path)
            results.append({"name": s.name, "action": "skipped", "head": head, "recorded": recorded,
                            "drift": bool(head and recorded and head != recorded),
                            "reason": "already initialized; init never moves a checkout (use pull/bump)"})
            continue
        if state in ("broken", "foreign"):
            # Never let `submodule update` run over files someone may still need.
            why = (".git exists but does not open as a repository (its git dir is missing or invalid)"
                   if state == "broken" else "the directory has files but no .git")
            refused = True
            results.append({"name": s.name, "action": "refused", "checkout": state,
                            "reason": f"{state} checkout at {display_path(root, child_dir(root, s))}: {why}; "
                                      "init will not overwrite it. Run `repair --dry-run`, and recover it by hand "
                                      f"as {REPAIR_DOC} describes"})
            continue
        if s.kind == "pointer":
            if not s.url:
                refused = True
                results.append({"name": s.name, "action": "refused",
                                "reason": f"no url in {MARKER} [repo \"{s.name}\"]"})
                continue
            dest = child_dir(root, s)
            cmd = ["clone", "-q", *(["--branch", s.branch] if s.branch else []), "--", s.url, str(dest)]
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                git(*cmd, cwd=root)
            results.append({"name": s.name, "action": "would-init" if args.dry_run else "initialized",
                            "command": "git " + " ".join(cmd)})
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
    def line(r: dict) -> str:
        extra = f"  ({r['reason']})" if "reason" in r else ""
        if r.get("drift"):
            extra += f"  [head {short(r['head'])} != gitlink {short(r['recorded'])}; kept]"
        return f"{r['action']:12} {r['name']}{extra}"

    emit(args, {"results": results}, "\n".join(line(r) for r in results) or "nothing selected")
    return 1 if refused else 0


# ---------------------------------------------------------------- pull

def pull_one(root: Path, s: Sub, args) -> dict:
    p = child_dir(root, s)
    branch = s.eff_branch(root)
    up = f"origin/{branch}"
    res = {"name": s.name, "branch": branch}
    if s.kind == "submodule" and s.eff_policy != "track" and not args.force:
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
    p = child_dir(root, s)
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
    by_path = {s.path: s for s in subs if s.kind == "submodule"}
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
            fetch(child_dir(root, s))
        for msg in check_commit(root, s, sha, require_clean=False):
            findings.append({"path": path, "level": "error", "message": msg})
        if is_initialized(root, s):
            p = child_dir(root, s)
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


POINTER_NO_GITLINK = ("is a pointer child: it has no gitlink, so there is nothing to bump or pin; "
                      "add it as a submodule (`add --submodule`) if its version must be recorded")


def cmd_bump(root: Path, subs: list[Sub], args) -> int:
    if not args.names and not args.all_track:
        raise UsageError("name submodules to bump, or pass --all-track")
    chosen = select(subs, args, lambda s: args.all_track and s.eff_policy == "track" and is_initialized(root, s))
    planned, refused, results = [], [], []
    for s in chosen:
        p = child_dir(root, s)
        res = {"name": s.name, "path": s.path, "policy": s.policy}
        try:
            if s.kind == "pointer":
                raise Refused(f"{s.name} {POINTER_NO_GITLINK}")
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
    return worktree_root(root) / wt_key(s) / branch.replace("/", "-")


def task_slug(task: str) -> str:
    return task.replace("/", "-")


def task_dir(root: Path, task: str) -> Path:
    return worktree_root(root) / TASKS_DIR / task_slug(task)


def worktrees_ignored(root: Path, wt_root: Path | None = None) -> bool:
    """True when the worktree root is ignored, or lies outside the workspace root."""
    rel = worktree_root_rel(root, wt_root)
    if rel is None:
        return True
    return git_rc("check-ignore", "-q", "--no-index", f"{rel}/probe", cwd=root) == 0


def ensure_gitignore(root: Path, dry_run: bool, wt_root: Path | None = None) -> bool:
    """Return True when .gitignore needs (or got) the worktree-root entry (default .worktrees/)."""
    if worktrees_ignored(root, wt_root):
        return False
    if not dry_run:
        gi = root / ".gitignore"
        text = gi.read_text() if gi.exists() else ""
        sep = "" if not text or text.endswith("\n") else "\n"
        gi.write_text(f"{text}{sep}# superproject-workspace: child worktrees\n{worktree_root_rel(root, wt_root)}/\n")
    return True


def assert_durable_store(root: Path, s: Sub | None = None) -> None:
    """Refuse to register worktrees (or create stores) that die with a superproject linked worktree.

    A submodule initialized inside `git worktree add` of the superproject keeps
    its store under `<main>/.git/worktrees/<id>/modules/`. Removing or pruning
    that outer worktree deletes the store, and every child worktree registered
    in it is orphaned. With `s=None` the check is for a new child store.
    """
    dirs = git_dirs(root)
    if not dirs:
        return
    root_gd, root_cd = dirs
    main = root_cd.parent if root_cd.name == ".git" else root_cd
    hint = f"rerun from the main checkout ({main}); no flag overrides this"
    if s is None:
        if root_gd != root_cd:
            raise Refused(f"{root} is a linked worktree of the superproject; a child store created here "
                          f"would be deleted with it. {hint}")
        return
    child = git_dirs(child_dir(root, s))
    if not child:
        return
    child_cd = child[1]
    if child_cd.is_relative_to(root_cd / "worktrees") or (root_gd != root_cd and child_cd.is_relative_to(root.resolve())):
        raise Refused(f"{s.name}'s git store ({child_cd}) belongs to a linked worktree of the superproject; "
                      f"worktrees registered there are orphaned when that worktree is removed. {hint}")


def plan_worktree(root: Path, s: Sub, branch: str, target: Path, base: str | None = None) -> tuple[list[str], str, bool]:
    """(git worktree add command, base, creates_branch) for `branch` of child `s` at `target`."""
    p = child_dir(root, s)
    if ref_exists(p, f"refs/heads/{branch}"):
        return ["worktree", "add", str(target), branch], branch, False
    if ref_exists(p, f"refs/remotes/origin/{branch}"):
        start = f"origin/{branch}"
        return ["worktree", "add", "--track", "-b", branch, str(target), start], start, True
    # Pinned children branch from the recorded baseline, not from upstream tip.
    start = base or (f"origin/{s.eff_branch(root)}" if s.eff_policy in ("track", "pointer")
                     else gitlink(root, s.path))
    if not start:
        raise Refused(f"{s.name} has no recorded gitlink yet (commit the superproject first) and no --base")
    return ["worktree", "add", "-b", branch, str(target), start], start, True


def rmdir_up(path: Path, stop: Path) -> list[str]:
    """rmdir `path` and its parents while empty, stopping below `stop`. Never removes contents."""
    stop, cur, removed = stop.resolve(), path.resolve(), []
    while cur != stop and cur.is_relative_to(stop):
        if cur.is_dir():
            try:
                cur.rmdir()
            except OSError:
                break
            removed.append(str(cur))
        cur = cur.parent
    return removed


def cmd_worktree(root: Path, subs: list[Sub], args) -> int:
    if args.wt_cmd == "list":
        chosen = [s for s in subs if is_initialized(root, s)]
        items = [dict(wt, submodule=s.name) for s in chosen
                 for wt in list_child_worktrees(root, s, include_unmanaged=args.all)]
        rows = [["SUBMODULE", "TASK", "BRANCH", "PATH", "STATE"]]
        for wt in items:
            state = ["prunable"] if wt["prunable"] else []
            if wt.get("dirty"):
                state.append(f"dirty({wt['dirty']})")
            if wt.get("untracked"):
                state.append(f"untracked({wt['untracked']})")
            if not wt["managed"]:
                state.append("outside worktree root")
            if wt["merged"]:
                state.append("merged: safe to remove")
            rows.append([wt["submodule"], wt["task"] or "-", wt["branch"] or "(detached)", wt["path"], ", ".join(state)])
        emit(args, {"worktrees": items}, table(rows) if items else "no child worktrees")
        return 0

    s = resolve(subs, args.submodule)
    p = child_dir(root, s)
    if not is_initialized(root, s):
        raise Refused(f"{s.name} is not initialized; run `init {s.name}` first")
    target = wt_path(root, s, args.branch)
    rel = display_path(root, target)

    if args.wt_cmd == "remove":
        cmd = ["worktree", "remove", *(["--force"] if args.force else []), str(target)]
        removed_dirs: list[str] = []
        if not args.dry_run:
            git(*cmd, cwd=p)
            git("worktree", "prune", cwd=p)
            if args.delete_branch:
                git("branch", "-D" if args.force else "-d", args.branch, cwd=p)
            removed_dirs = rmdir_up(target.parent, worktree_root(root))
        emit(args, {"removed": rel, "empty_parents_removed": [display_path(root, Path(d)) for d in removed_dirs],
                    "dry_run": args.dry_run}, f"{'would remove' if args.dry_run else 'removed'} {rel}")
        return 0

    # add
    assert_durable_store(root, s)
    if target.exists():
        raise Refused(f"{rel} already exists")
    if not args.no_fetch:
        fetch(p)
    cmd, base, _ = plan_worktree(root, s, args.branch, target, args.base)
    gi = ensure_gitignore(root, args.dry_run)
    if not args.dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        git(*cmd, cwd=p)
    data = {"path": rel, "branch": args.branch, "base": base, "gitignore_updated": gi, "dry_run": args.dry_run}
    emit(args, data, f"{'would create' if args.dry_run else 'created'} {rel} on {args.branch} from {base}"
         + (f"\nadded {worktree_root_rel(root)}/ to .gitignore" if gi else ""))
    return 0


# ---------------------------------------------------------------- tasks

def check_branch_name(root: Path, name: str, what: str) -> None:
    if not name or git_rc("check-ref-format", "--branch", name, cwd=root) != 0:
        raise UsageError(f"{what} {name!r} is not a valid branch name (see `git check-ref-format --branch`)")


def rollback_members(root: Path, entries: list[tuple[Sub, Path, bool]], branch: str) -> list[str]:
    """Undo worktrees this call created: `git worktree remove`, then delete branches it created."""
    base, undone = worktree_root(root), []
    for s, target, created_branch in reversed(entries):
        p = child_dir(root, s)
        if target.resolve() in {Path(b["worktree"]).resolve() for b in worktree_blocks(p)}:
            git("worktree", "remove", "--force", str(target), cwd=p, check=False)  # created seconds ago by us
        git("worktree", "prune", cwd=p, check=False)
        if created_branch and ref_exists(p, f"refs/heads/{branch}"):
            git("branch", "-D", branch, cwd=p, check=False)
        rmdir_up(target, base)
        undone.append(s.name)
    return undone


def task_open(root: Path, subs: list[Sub], args) -> int:
    check_branch_name(root, args.task, "TASK")
    branch = args.branch or args.task
    check_branch_name(root, branch, "--branch")
    members: list[Sub] = []
    for ident in args.children:
        s = resolve(subs, ident)
        if s not in members:
            members.append(s)
    bases: dict[str, str] = {}
    for spec in args.base or []:
        ident, sep, rev = spec.partition("=")
        if not sep or not rev:
            raise UsageError(f"--base {spec!r}: expected CHILD=REV")
        s = resolve(subs, ident)
        if s not in members:
            raise UsageError(f"--base names {s.name}, which is not a member of this call")
        bases[s.name] = rev
    tdir = task_dir(root, args.task)
    targets = {s.name: tdir / wt_key(s) for s in members}
    for a in members:
        for b in members:
            if a is not b and targets[b.name].is_relative_to(targets[a.name]):
                raise UsageError(f"{b.name} would nest inside {a.name} in the task directory; open them in separate tasks")

    # Phase 1: check every member; change nothing unless all pass.
    plans, problems = [], []
    for s in members:
        target = targets[s.name]
        try:
            state = checkout_state(root, s)
            if state != "ok":
                raise Refused(f"checkout is {state}; run `init {s.name}` first" if state == "absent"
                              else f"checkout is {state}; see `repair`")
            assert_durable_store(root, s)
            p = child_dir(root, s)
            blocks = worktree_blocks(p)
            here = next((b for b in blocks if Path(b["worktree"]).resolve() == target.resolve()), None)
            if here:
                if block_branch(here) != branch:
                    raise Refused(f"{display_path(root, target)} exists on {block_branch(here) or 'a detached HEAD'}, not {branch}")
                plans.append((s, target, None, block_branch(here), False))
                continue
            if os.path.lexists(target):
                raise Refused(f"{display_path(root, target)} exists and is not a worktree of {s.name}")
            for i, b in enumerate(blocks):
                if block_branch(b) == branch:
                    where = display_path(root, p) if i == 0 else display_path(root, Path(b["worktree"]))
                    raise Refused(f"branch {branch} is already checked out at {where}")
            if not args.no_fetch and (err := fetch(p)):
                print(f"warning: {s.name}: fetch failed ({err}); using local refs", file=sys.stderr)
            cmd, base, creates = plan_worktree(root, s, branch, target, bases.get(s.name))
            plans.append((s, target, cmd, base, creates))
        except Refused as e:
            problems.append(f"{s.name}: {e}")
    if problems:
        raise Refused("task open checked every member first and changed nothing:\n  " + "\n  ".join(problems))

    # Phase 2: create; roll back this call's worktrees on any failure.
    gi = ensure_gitignore(root, args.dry_run)
    results, created = [], []
    for s, target, cmd, base, creates in plans:
        r = {"child": s.name, "path": display_path(root, target), "branch": branch, "base": base}
        if cmd is None:
            r["action"] = "exists"
        elif args.dry_run:
            r.update(action="would-create", command="git " + " ".join(cmd))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                git(*cmd, cwd=child_dir(root, s))
            except Refused as e:
                undone = rollback_members(root, created + [(s, target, creates)], branch)
                for prev in results:
                    if prev["action"] == "created":
                        prev["action"] = "rolled-back"
                r.update(action="failed", reason=str(e))
                results.append(r)
                print(f"refused: task open failed at {s.name}; rolled back this call's worktrees "
                      f"({', '.join(undone)}): {e}", file=sys.stderr)
                emit(args, {"task": args.task, "branch": branch, "path": display_path(root, tdir),
                            "members": results, "dry_run": False}, "")
                return 1
            created.append((s, target, creates))
            r["action"] = "created"
        results.append(r)
    lines = [f"{r['action']:12} {r['child']:16} {r['path']}  ({branch} from {r['base']})" for r in results]
    lines.append(f"task directory: {display_path(root, tdir)}  (open this one directory in your editor or agent)")
    if gi:
        lines.append(f"added {worktree_root_rel(root)}/ to .gitignore")
    emit(args, {"task": args.task, "branch": branch, "path": display_path(root, tdir), "members": results,
                "gitignore_updated": gi, "dry_run": args.dry_run}, "\n".join(lines))
    return 0


def stray_paths(root: Path, d: Path, members: set[Path]) -> list[str]:
    """Entries under a task directory that are not on the way to a member worktree."""
    out: list[str] = []

    def walk(x: Path) -> None:
        for e in sorted(x.iterdir()):
            r = e.resolve()
            if r in members:
                continue
            if e.is_dir() and not e.is_symlink() and any(m.is_relative_to(r) for m in members):
                walk(e)
            else:
                out.append(display_path(root, e))

    if d.is_dir():
        walk(d)
    return out


def collect_tasks(root: Path, subs: list[Sub]) -> dict[str, dict]:
    """Tasks derived from each child's `git worktree list`; no state file."""
    tbase = worktree_root(root) / TASKS_DIR
    tasks: dict[str, dict] = {}
    for s in subs:
        if not is_initialized(root, s):
            continue
        for w in list_child_worktrees(root, s):
            if w["task"]:
                tasks.setdefault(w["task"], {"members": []})["members"].append(dict(w, child=s.name, kind=s.kind))
    if tbase.is_dir():
        for d in sorted(tbase.iterdir()):
            if d.is_dir():
                tasks.setdefault(d.name, {"members": []})
    for name, info in tasks.items():
        m = info["members"]
        info.update(task=name, path=display_path(root, tbase / name),
                    stray_dirs=stray_paths(root, tbase / name, {Path(x["abs_path"]) for x in m}),
                    ready_to_close=bool(m) and all(not x["prunable"] and not x["dirty"] and not x["untracked"]
                                                   and x["merged"] for x in m))
    return dict(sorted(tasks.items()))


def pick_task(root: Path, subs: list[Sub], task: str) -> dict:
    tasks = collect_tasks(root, subs)
    if task_slug(task) not in tasks:
        raise UsageError(f"no task {task!r} under {display_path(root, worktree_root(root) / TASKS_DIR)} "
                         f"(known: {', '.join(tasks) or 'none'})")
    return tasks[task_slug(task)]


def task_list(root: Path, subs: list[Sub], args) -> int:
    tasks = [pick_task(root, subs, args.task)] if args.task else list(collect_tasks(root, subs).values())
    blocks = []
    for t in tasks:
        rows = [["CHILD", "BRANCH", "PATH", "STATE"]]
        for m in t["members"]:
            state = ["prunable"] if m["prunable"] else []
            if m["dirty"]:
                state.append(f"dirty({m['dirty']})")
            if m["untracked"]:
                state.append(f"untracked({m['untracked']})")
            if m["unpushed"]:
                state.append(f"unpushed({m['unpushed']})")
            state.append("merged" if m["merged"] else "not merged")
            rows.append([m["child"], m["branch"] or "(detached)", m["path"], ", ".join(state)])
        head = f"task {t['task']}  ({t['path']})" + ("  ready to close" if t["ready_to_close"] else "")
        stray = f"\n  stray: {', '.join(t['stray_dirs'])}" if t["stray_dirs"] else ""
        blocks.append(head + "\n" + table(rows) + stray)
    emit(args, {"tasks": tasks}, "\n\n".join(blocks) or "no tasks")
    return 0


def task_close(root: Path, subs: list[Sub], args) -> int:
    t = pick_task(root, subs, args.task)
    members = t["members"]
    if args.children:
        names = {resolve(subs, n).name for n in args.children}
        missing = names - {m["child"] for m in members}
        if missing:
            raise UsageError(f"not members of task {args.task}: {', '.join(sorted(missing))}")
        members = [m for m in members if m["child"] in names]
    if not members:
        raise UsageError(f"task {args.task} has no member worktrees (stray: {', '.join(t['stray_dirs']) or 'none'})")
    problems = []
    for m in members:
        if m["prunable"]:
            continue
        if m["dirty"] or m["untracked"]:
            problems.append(f"{m['child']}: {m['dirty']} modified, {m['untracked']} untracked file(s)")
        if args.delete_branch and m["branch"] and not m["merged"]:
            extra = f", {m['unpushed']} unpushed commit(s)" if m["unpushed"] else ""
            problems.append(f"{m['child']}: branch {m['branch']} is not merged{extra}")
    if problems and not args.force:
        raise Refused("task close checked every member and changed nothing:\n  " + "\n  ".join(problems)
                      + "\ncommit/push or discard first, or pass --force to discard them")

    base, results = worktree_root(root), []
    for m in members:
        s = resolve(subs, m["child"])
        p = child_dir(root, s)
        cmd = (["worktree", "prune"] if m["prunable"]
               else ["worktree", "remove", *(["--force"] if args.force else []), m["abs_path"]])
        r = {"child": m["child"], "path": m["path"], "branch": m["branch"], "commands": ["git " + " ".join(cmd)]}
        delete = args.delete_branch and m["branch"]
        if delete:
            r["commands"].append(f"git branch {'-D' if args.force else '-d'} {m['branch']}")
        if not args.dry_run:
            git(*cmd, cwd=p)
            if delete and (args.force or git_rc("branch", "-d", m["branch"], cwd=p) != 0):
                # `-d` judges against HEAD/upstream; `merged` was proven against origin/<branch>.
                git("branch", "-D", m["branch"], cwd=p)
            rmdir_up(Path(m["abs_path"]).parent, base)
        r["action"] = "would-close" if args.dry_run else "closed"
        results.append(r)
    lines = [f"{r['action']:12} {r['child']:16} {r['path']}" + (f"  (branch {r['branch']} deleted)"
             if args.delete_branch and r["branch"] and not args.dry_run else "") for r in results]
    if not args.dry_run:
        lines.append("next: `pull` the members, then `bump <members> --commit` once their changes are on origin")
    emit(args, {"task": args.task, "members": results, "dry_run": args.dry_run}, "\n".join(lines))
    return 0


def cmd_task(root: Path, subs: list[Sub], args) -> int:
    return {"open": task_open, "list": task_list, "close": task_close}[args.task_cmd](root, subs, args)


# ---------------------------------------------------------------- health / repair

def store_dirs(modules: Path, prefix: str = "", nested: bool = False) -> dict[str, Path]:
    """{submodule name: store dir} under a `.git/modules`-style directory.

    A store is a directory with HEAD. Names with slashes nest as directories.
    With `nested`, also descend into each store's own `modules/`.
    """
    out: dict[str, Path] = {}
    if not modules.is_dir():
        return out
    for d in sorted(modules.iterdir()):
        if not d.is_dir() or d.is_symlink():
            continue
        name = f"{prefix}{d.name}"
        if (d / "HEAD").is_file():
            out[name] = d
            if nested:
                out.update({f"{name}//{k}": v for k, v in store_dirs(d / "modules", nested=True).items()})
        else:
            out.update(store_dirs(d, name + "/", nested))
    return out


def read_gitfile(d: Path) -> Path | None:
    """Target of `<d>/.git` when it is a gitfile, else None."""
    g = d / ".git"
    if not g.is_file():
        return None
    m = re.match(r"gitdir:\s*(.+)", g.read_text().strip())
    if not m:
        return None
    target = Path(m.group(1))
    return target if target.is_absolute() else d / target


def checkouts_under(base: Path):
    """Directories under `base` that contain `.git`; does not descend into them."""
    stack = [base]
    while stack:
        cur = stack.pop()
        try:
            entries = sorted(cur.iterdir(), reverse=True)
        except OSError:
            continue
        for e in entries:
            if not e.is_dir() or e.is_symlink():
                continue
            if os.path.lexists(e / ".git"):
                yield e
            else:
                stack.append(e)


def child_for_dir(base: Path, d: Path, subs: list[Sub]) -> Sub | None:
    """Map a checkout under the worktree root back to its child by the two layouts."""
    parts = d.resolve().relative_to(base.resolve()).parts
    key = "/".join(parts[2:]) if parts and parts[0] == TASKS_DIR else "/".join(parts[:-1])
    return next((s for s in subs if wt_key(s) == key), None)


def scan_health(root: Path, subs: list[Sub]) -> list[dict]:
    """Findings about checkouts, worktrees, and stores, shared by `audit` and `repair`."""
    f: list[dict] = []

    def add(level: str, code: str, subject: str, message: str, fix: str = "", **extra) -> None:
        f.append({"level": level, "code": code, "subject": subject, "message": message, "fix": fix, **extra})

    dirs = git_dirs(root)
    root_gd, root_cd = dirs if dirs else (None, None)
    base = worktree_root(root)
    stores: dict[str, Path] = {}
    for s in subs:
        state = checkout_state(root, s)
        if state in ("broken", "foreign"):
            add("error", "checkout-broken", s.name,
                f"{display_path(root, child_dir(root, s))} is {state}: "
                + (".git does not open as a repository (git dir missing?)" if state == "broken" else "files without .git"),
                f"`repair --dry-run` lists it; recover by hand: move it aside, `init {s.name}`, "
                f"copy your files back ({REPAIR_DOC})",
                child=s.name, path=str(child_dir(root, s)))
            continue
        if state != "ok":
            continue
        cd = git_dirs(child_dir(root, s))
        if cd:
            stores[s.name] = cd[1]
        for b in worktree_blocks(child_dir(root, s))[1:]:
            if "prunable" in b:
                add("info", "worktree-prunable", s.name,
                    f"{display_path(root, Path(b['worktree']))} is gone but still registered",
                    "repair --prune", child=s.name, path=b["worktree"])

    if base.is_dir():
        for d in checkouts_under(base):
            target = read_gitfile(d)
            if target is None or target.exists():
                continue
            s = child_for_dir(base, d, subs)
            path = display_path(root, d)
            admin = stores[s.name] / "worktrees" / target.name if s and s.name in stores else None
            if admin and admin.is_dir():
                back = Path((admin / "gitdir").read_text().strip()) if (admin / "gitdir").is_file() else None
                if not back or not back.exists() or back.resolve() == (d / ".git").resolve():
                    add("warn", "worktree-relinkable", s.name,
                        f"{path}: .git points to a store path that moved; its admin dir still exists",
                        "repair", child=s.name, path=str(d), admin=str(admin))
                    continue
            cause = ("superproject-worktree-removed" if re.search(r"/worktrees/[^/]+/modules/", target.as_posix())
                     else "store-missing")
            add("error", "worktree-orphan", s.name if s else path,
                f"{path}: .git points to {target}, which no longer exists ({cause}); "
                "unpushed commits made there are gone, the files are not",
                "repair --reattach (keeps the files) or repair --delete-orphans PATH",
                child=s.name if s else None, path=str(d), cause=cause)

    if root_cd and (root_cd / "worktrees").is_dir():
        for adm in sorted((root_cd / "worktrees").iterdir()):
            gd = adm / "gitdir"
            wt = Path(gd.read_text().strip()).parent if gd.is_file() else adm
            mods = store_dirs(adm / "modules", nested=True)
            add("warn" if mods else "info", "superproject-worktrees", display_path(root, wt),
                "linked worktree of the superproject"
                + (f" with initialized submodules ({', '.join(sorted(mods))}); child worktrees opened from them "
                   "die with it" if mods else ""),
                "keep child work in `worktree add` / `task open` from the main checkout; "
                "`git worktree remove` it when its outer-only change is done", path=str(wt))
            for name, store in mods.items():
                wdir = store / "worktrees"
                for w in sorted(wdir.iterdir()) if wdir.is_dir() else []:
                    if (w / "gitdir").is_file():
                        cwt = Path((w / "gitdir").read_text().strip()).parent
                        add("warn", "worktree-at-risk", name,
                            f"{display_path(root, cwt)} is registered in the store of superproject worktree "
                            f"{display_path(root, wt)}; removing that worktree orphans it",
                            "push its branch, `git worktree remove` it, then reopen it from the main checkout",
                            path=str(cwt))

    declared = set(_load_cfg(root, ".gitmodules", "submodule"))
    keys = git("config", "--local", "--name-only", "--get-regexp", r"^submodule\.", cwd=root, check=False)
    configured = {k[len("submodule."):].rpartition(".")[0] for k in keys.splitlines() if k}
    for n in sorted(configured - declared - {""}):
        add("info", "stale-submodule-config", n,
            f".git/config still has submodule.{n}.* but .gitmodules does not declare it",
            "repair --prune", name=n)
    if root_cd:
        # A store's path follows the name the submodule had when it was first cloned, so a
        # renamed or moved child keeps using a store that matches no declared name.
        in_use = set()
        for s in subs:
            gd = git_dirs(child_dir(root, s)) if child_dir(root, s).exists() else None
            if gd:
                in_use.add(gd[1].resolve())
        for n, store in store_dirs(root_cd / "modules").items():
            if n not in declared and store.resolve() not in in_use:
                add("info", "stale-module-store", n,
                    f"{display_path(root, store)} stores an undeclared submodule (it may hold unpushed commits)",
                    f"manual: check for unpushed work, then delete it by hand ({REPAIR_DOC}); never automatic",
                    path=str(store))
    return f


def file_stats(d: Path) -> tuple[int, str | None]:
    count, latest = 0, 0.0
    for dirpath, dirnames, filenames in os.walk(d):
        for n in filenames:
            count += 1
            try:
                latest = max(latest, os.lstat(os.path.join(dirpath, n)).st_mtime)
            except OSError:
                pass
    import datetime
    return count, (datetime.datetime.fromtimestamp(latest).isoformat(timespec="seconds") if count else None)


def reattach(root: Path, s: Sub, d: Path, base: str, dry_run: bool) -> dict:
    """Give an orphaned worktree a new admin dir in the child's durable store, keeping its files."""
    p = child_dir(root, s)
    rescue, i = f"rescue/{d.name}", 2
    while ref_exists(p, f"refs/heads/{rescue}"):
        rescue, i = f"rescue/{d.name}-{i}", i + 1
    holder = d.parent / ".superproject-reattach"
    tmp = holder / d.name
    steps = [f"git -C {display_path(root, p)} worktree add --no-checkout -b {rescue} {display_path(root, tmp)} {base}",
             f"point {display_path(root, d)}/.git and the new admin dir at each other",
             f"git -C {display_path(root, d)} reset -q   (index from {rescue}; files untouched)"]
    res = {"kind": "reattach", "path": str(d), "child": s.name, "branch": rescue, "base": base, "steps": steps}
    if dry_run:
        return res
    if os.path.lexists(holder):
        raise Refused(f"{display_path(root, holder)} exists (a previous reattach was interrupted?); inspect and remove it")
    holder.mkdir()
    try:
        git("worktree", "add", "--no-checkout", "-b", rescue, str(tmp), base, cwd=p)
        admin = Path(git("rev-parse", "--absolute-git-dir", cwd=tmp))
        (d / ".git").write_text(f"gitdir: {admin}\n")
        (admin / "gitdir").write_text(f"{d.resolve() / '.git'}\n")
        (tmp / ".git").unlink()
    finally:
        rmdir_up(tmp, d.parent)
    git("reset", "-q", cwd=d)
    top = git("rev-parse", "--show-toplevel", cwd=d, check=False)
    if not top or Path(top).resolve() != d.resolve():
        raise Refused(f"reattach of {display_path(root, d)} did not verify (rev-parse --show-toplevel gave {top!r})")
    return res


def cmd_repair(root: Path, subs: list[Sub], args) -> int:
    if args.delete_orphans and not args.paths:
        raise UsageError("--delete-orphans needs explicit PATH arguments; list orphans with `repair --dry-run`")
    if args.delete_orphans and args.reattach:
        raise UsageError("pass either --reattach or --delete-orphans, not both")
    if args.base and not args.reattach:
        raise UsageError("--base only applies to --reattach")

    def norm(p: str) -> Path:
        q = Path(p).expanduser()
        if not q.is_absolute():
            q = Path.cwd() / q if (Path.cwd() / q).exists() or not (root / q).exists() else root / q
        return q.resolve()

    wanted = {norm(p) for p in args.paths}
    findings = scan_health(root, subs)
    by_name = {s.name: s for s in subs}

    def picked(x: dict) -> bool:
        return not wanted or Path(x["path"]).resolve() in wanted

    orphans = {Path(x["path"]).resolve(): x for x in findings if x["code"] == "worktree-orphan"}
    if args.delete_orphans:
        bad = [str(w) for w in wanted if w not in orphans]
        if bad:
            raise Refused(f"not confirmed orphans by the scan, nothing deleted: {', '.join(bad)}")

    actions: list[dict] = []
    handled: set[int] = set()

    def run(x: dict, action: dict, fn) -> None:
        handled.add(id(x))
        try:
            if not args.dry_run:
                fn()
            action["result"] = "planned" if args.dry_run else "done"
        except Refused as e:
            action.update(result="failed", reason=str(e))
        actions.append(action)

    for x in findings:
        if x["code"] == "worktree-relinkable" and picked(x):
            p, d = child_dir(root, by_name[x["child"]]), Path(x["path"])

            def relink(p=p, d=d) -> None:
                git("worktree", "repair", str(d), cwd=p)
                top = git("rev-parse", "--show-toplevel", cwd=d, check=False)
                if not top or Path(top).resolve() != d.resolve():
                    raise Refused(f"relink of {display_path(root, d)} did not verify")
            run(x, {"kind": "relink", "path": str(d), "command": f"git -C {display_path(root, p)} worktree repair {d}"}, relink)

    if args.prune:
        pruned: set[str] = set()
        for x in findings:
            if x["code"] == "worktree-prunable" and x["child"] not in pruned:
                pruned.add(x["child"])
                p = child_dir(root, by_name[x["child"]])
                run(x, {"kind": "prune", "path": str(p), "command": f"git -C {display_path(root, p)} worktree prune"},
                    lambda p=p: git("worktree", "prune", cwd=p))
            elif x["code"] == "worktree-prunable":
                handled.add(id(x))
            elif x["code"] == "stale-submodule-config":
                n = x["name"]
                run(x, {"kind": "remove-config", "path": f"submodule.{n}",
                        "command": f"git config --remove-section submodule.{n}"},
                    lambda n=n: git("config", "--remove-section", f"submodule.{n}", cwd=root))

    if args.reattach:
        for x in orphans.values():
            if not picked(x):
                continue
            s = by_name.get(x["child"]) if x["child"] else None
            d = Path(x["path"])
            if not s or not is_initialized(root, s):
                handled.add(id(x))
                actions.append({"kind": "reattach", "path": str(d), "result": "skipped",
                                "reason": "cannot map it to an initialized child; move it by hand or --delete-orphans"})
                continue
            try:
                assert_durable_store(root, s)
                base = args.base or (f"origin/{s.eff_branch(root)}" if s.kind == "pointer" else gitlink(root, s.path))
                if not base:
                    raise Refused(f"{s.name} has no recorded gitlink; pass --base")
                actions.append(reattach(root, s, d, base, args.dry_run)
                               | {"result": "planned" if args.dry_run else "done"})
            except Refused as e:
                actions.append({"kind": "reattach", "path": str(d), "result": "failed", "reason": str(e)})
            handled.add(id(x))

    if args.delete_orphans:
        for w in sorted(wanted):
            x = orphans[w]
            n, latest = file_stats(w)
            run(x, {"kind": "delete", "path": str(w), "files": n, "latest_mtime": latest,
                    "command": f"delete {display_path(root, w)} ({n} files, newest {latest})"},
                lambda w=w: (shutil.rmtree(w), rmdir_up(w.parent, worktree_root(root))))

    flag_for = {"worktree-relinkable": "(default)", "worktree-prunable": "--prune", "stale-submodule-config": "--prune",
                "worktree-orphan": "--reattach | --delete-orphans PATH"}
    # A dry run counts what the planned actions would leave; a real run rescans.
    remaining = [x for x in findings if id(x) not in handled] if args.dry_run else scan_health(root, subs)
    lines = []
    for x in findings:
        how = flag_for.get(x["code"], "manual")
        lines.append(f"{x['level']:5} {x['code']:24} {x['subject']}: {x['message']}\n      handled by: {how}"
                     + (f"; {x['fix']}" if how == "manual" else ""))
    verb = "would" if args.dry_run else "did"
    for a in actions:
        detail = a.get("command") or "; ".join(a.get("steps", []))
        status = a["result"] if a["result"] not in ("planned", "done") else verb
        lines.append(f"{status}: {a['kind']:13} {detail}" + (f"  ({a['reason']})" if a.get("reason") else ""))
    lines.append(f"\n{len(remaining)} finding(s) remaining")
    emit(args, {"findings": findings, "actions": actions, "remaining": len(remaining), "dry_run": args.dry_run},
         "\n".join(lines) if findings else "no worktree or store problems found")
    failed = any(a["result"] == "failed" for a in actions) or any(x["level"] == "error" for x in remaining)
    return 1 if failed else 0


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


def audit_pointer(root: Path, s: Sub, add) -> None:
    raw = Path(s.path).expanduser()
    if raw.is_absolute():
        add("info", "pointer-path-absolute", s.name,
            f"path {s.path} is absolute (or ~); other clones of this repo need the same layout",
            "prefer repos/<name> inside the root, or a path relative to it")
    if not s.url:
        add("error", "pointer-url-missing", s.name, f"{MARKER} [repo \"{s.name}\"] has no url")
    target = child_dir(root, s)
    inside = target.resolve().is_relative_to(root.resolve())
    if inside:
        rel = display_path(root, target)
        if git("ls-files", "--", rel, cwd=root, check=False):
            add("error", "pointer-tracked", s.name,
                f"{rel} is tracked by the outer repo; a pointer clone must not be committed into it",
                f"git rm -r --cached -- {rel}, then ignore it")
        elif not path_ignored(root, rel):
            add("warn", "pointer-not-ignored", s.name, f"{rel} is not gitignored; `git add -A` would sweep it in",
                f"echo '/{rel}/' >> .gitignore")
    if checkout_state(root, s) == "ok" and s.url:
        origin = git("remote", "get-url", "origin", cwd=target, check=False)
        if origin != s.url:
            add("warn", "pointer-url-mismatch", s.name,
                f"clone's origin is {origin or '(none)'}, {MARKER} says {s.url}",
                f"git -C {display_path(root, target)} remote set-url origin {s.url}, or fix {MARKER}")


def cmd_audit(root: Path, subs: list[Sub], args) -> int:
    f: list[dict] = []

    def add(level: str, code: str, subject: str, message: str, fix: str = "") -> None:
        f.append({"level": level, "code": code, "subject": subject, "message": message, "fix": fix})

    if not subs:
        # A root that only has the marker is a fresh workspace, not a broken one.
        fresh = not (root / ".gitmodules").exists() and (root / MARKER).exists()
        add("info" if fresh else "error", "no-submodules", MARKER if fresh else ".gitmodules",
            "no children declared" + (" yet" if fresh else ""), "add URL [PATH] to add one")
    for s in subs:
        if s.kind == "pointer":
            audit_pointer(root, s, add)
            continue
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
        if st["checkout"] in ("broken", "foreign"):
            continue  # reported as checkout-broken by scan_health below
        if not st["initialized"]:
            if s.eff_policy != "lazy":
                add("warn", "uninitialized", s.name, f"{s.eff_policy} child is not initialized", f"init {s.name}")
            continue
        configured = git("config", "--get", f"submodule.{s.name}.url", cwd=root, check=False)
        if not configured:
            add("info", "submodule-config-missing", s.name,
                f"checkout is fine but .git/config has no submodule.{s.name}.url (plain git treats it as inactive)",
                f"git submodule init -- {s.path}")
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
        for w in st["worktrees"]:  # prunable ones are reported by scan_health below
            if w["merged"] and not w["prunable"]:
                add("info", "worktree-merged", s.name, f"{w['path']} ({w['branch']}) is merged",
                    f"task close {w['task']} --delete-branch" if w["task"]
                    else f"worktree remove {s.name} {w['branch']} --delete-branch")
        for w in st["warnings"]:
            add("warn", "state", s.name, w)

    for x in scan_health(root, subs):
        add(x["level"], x["code"], x["subject"], x["message"], x["fix"])
    cur = git("symbolic-ref", "-q", "--short", "HEAD", cwd=root, check=False)
    default = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", cwd=root, check=False).removeprefix("origin/")
    if not cur or (cur != default if default else cur not in ("main", "master")):
        add("info", "outer-branch", "superproject",
            f"the superproject is {'on ' + cur if cur else 'detached'}, not its default branch "
            f"{default or 'main/master'}; cross-repo work belongs on child branches",
            f"git switch {default or 'main'} once this outer-only change is merged")
    if worktree_root_rel(root) is None:
        add("info", "worktree-outside-root", "worktree root",
            f"child worktrees live outside the workspace ({worktree_root(root)}); "
            "an agent started at the root does not see them without add-dir")
    agents = find_agents_file(root)
    if not agents or AGENTS_BEGIN not in agents.read_text():
        add("warn", "agents-block", agents.name if agents else "AGENTS.md",
            "no superproject-workspace guidance block for agents", "adopt")
    claude = root / "CLAUDE.md"
    if agents and agents.name == "AGENTS.md" and claude.is_file() and not claude.is_symlink():
        ctext = claude.read_text()
        if "@AGENTS.md" not in ctext and AGENTS_BEGIN in agents.read_text() and AGENTS_BEGIN not in ctext:
            add("warn", "agents-not-loaded", "CLAUDE.md",
                "the guidance block is only in AGENTS.md, and Claude Code reads CLAUDE.md instead when both exist",
                "add a line `@AGENTS.md` to CLAUDE.md, or make CLAUDE.md a symlink to AGENTS.md")
    if not worktrees_ignored(root):
        add("warn", "worktrees-not-ignored", ".gitignore", f"{worktree_root_rel(root)}/ is not ignored", "adopt")
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
            (agents, AGENTS_BEGIN, AGENTS_END, agents_asset(root, subs)),
            (jf, JUST_BEGIN, JUST_END, "justfile.snippet"),
        ):
            block = extract_block(target.read_text(), begin, end) if target else None
            want = extract_block(render_asset(asset, worktree_label(root)), begin, end)
            if block and want and block != want:
                add("warn", "managed-block-stale", target.name,
                    f"managed block differs from superproject-workspace {__version__}", "adopt")
    # The repo map is generated from the manifests; compare what is written with what they say now.
    if agents and AGENTS_BEGIN in agents.read_text():
        block, doc = render_repo_map(root, subs)
        mf = map_file(root)
        stale = extract_block(agents.read_text(), MAP_BEGIN, MAP_END) != block
        if doc is not None:
            stale = stale or not mf.exists() or extract_block(mf.read_text(), MAP_BEGIN, MAP_END) != doc
        if stale:
            add("warn", "repo-map-stale", agents.name, "the repo map does not match .gitmodules/.superproject",
                "adopt (rewrites the map; `add` refreshes it too)")
        if mf is None and len(subs) > MAP_INLINE_MAX:
            add("info", "repo-map-large", agents.name,
                f"{len(subs)} repositories listed inline in {agents.name} (> {MAP_INLINE_MAX})",
                f"git config -f {MARKER} workspace.map-file docs/repos.md, then adopt")
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
    if any(s.kind == "submodule" for s in subs) and \
            git("config", "--get", "push.recurseSubmodules", cwd=root, check=False) not in ("check", "on-demand"):
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

def render_asset(name: str, worktree_label: str = WORKTREE_DIR) -> str:
    """Asset text with `{{WORKTREE_ROOT}}` filled in (other `{{...}}` are just syntax, left alone)."""
    path = SKILL_ASSETS / name
    if not path.exists():
        raise UsageError(f"asset {name} not found; run adopt from the installed skill, not a vendored copy")
    return path.read_text().replace("{{WORKTREE_ROOT}}", worktree_label)


def worktree_label(root: Path, wt_root: Path | None = None) -> str:
    return worktree_root_rel(root, wt_root) or str(wt_root or worktree_root(root))


def agents_asset(root: Path, subs: list[Sub], mode: str | None = None) -> str:
    """The pointer template for a home repo without submodules, else the submodule one."""
    if any(s.kind == "submodule" for s in subs):
        return "agents-block.md.template"
    mode = mode or marker_get(root, "workspace.mode") or "submodule"
    return "agents-block-pointer.md.template" if mode == "pointer" else "agents-block.md.template"


def map_file(root: Path) -> Path | None:
    v = marker_get(root, "workspace.map-file")
    if not v:
        return None
    p = Path(v).expanduser()
    return p if p.is_absolute() else root / p


def _map_table(subs: list[Sub]) -> list[str]:
    rows = ["| Name | Role | Path | Kind | Tier | If missing |", "|---|---|---|---|---|---|"]
    for s in sorted(subs, key=lambda s: s.name):
        kind = "pointer" if s.kind == "pointer" else f"submodule ({s.eff_policy})"
        role = (s.role or "-").replace("|", "\\|")
        rows.append(f"| {s.name} | {role} | `{s.path}` | {kind} | {s.tier or '-'} | `init {s.name}` |")
    return rows


def render_repo_map(root: Path, subs: list[Sub]) -> tuple[str, str | None]:
    """(block for the agents file, full map block for map-file or None)."""
    intro = ("Commands are `superproject.py` subcommands (`just sub-<cmd>` once adopted). Inside a "
             "repository, its own AGENTS.md/CLAUDE.md is authoritative.")
    mf = map_file(root)
    if not subs:
        body = "No repositories yet; add one with `add URL [PATH]`."
        return f"{MAP_BEGIN}\n## Repositories\n\n{body}\n{MAP_END}", (
            f"{MAP_BEGIN}\n# Repository map\n\n{body}\n{MAP_END}" if mf else None)
    if mf is None:
        return f"{MAP_BEGIN}\n## Repositories\n\n{intro}\n\n" + "\n".join(_map_table(subs)) + f"\n{MAP_END}", None
    tiers: dict[str, list[Sub]] = {}
    for s in subs:
        tiers.setdefault(s.tier or "untiered", []).append(s)
    counts = ", ".join(f"{k}: {len(v)}" for k, v in sorted(tiers.items()))
    rel = display_path(root, mf)
    block = (f"{MAP_BEGIN}\n## Repositories\n\n{len(subs)} repositories ({counts}). The full map, with "
             f"roles, paths, and the command for a missing one, is in [`{rel}`]({rel}); read it before "
             f"searching for a repository.\n{MAP_END}")
    sections = [f"## {k}\n\n" + "\n".join(_map_table(v)) for k, v in sorted(tiers.items())]
    doc = f"{MAP_BEGIN}\n# Repository map\n\n{intro}\n\n" + "\n\n".join(sections) + f"\n{MAP_END}"
    return block, doc


def update_repo_map(root: Path, subs: list[Sub], dry_run: bool, actions: list[dict], *, create: bool = True) -> None:
    """Upsert the repo-map block (and the map-file document when configured)."""
    agents = find_agents_file(root) or (root / "AGENTS.md" if create else None)
    block, doc = render_repo_map(root, subs)
    targets = [(agents, block)] if agents else []
    if doc is not None:
        targets.append((map_file(root), doc))
    for path, content in targets:
        old = path.read_text() if path.exists() else ""
        new = upsert_block(old, MAP_BEGIN, MAP_END, content)
        if new != old:
            actions.append({"kind": "file", "target": display_path(root, path), "detail": "upsert repo map"})
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(new)


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


def scaffold(root: Path, args, actions: list[dict], wt_root: Path | None = None,
             subs: list[Sub] | None = None, mode: str | None = None) -> None:
    """Managed files and local git config shared by `adopt` and `new` (idempotent)."""
    subs = subs or []
    label = worktree_label(root, wt_root)
    if not args.no_agents:
        agents = find_agents_file(root) or root / "AGENTS.md"
        old = agents.read_text() if agents.exists() else ""
        new = upsert_block(old, AGENTS_BEGIN, AGENTS_END, render_asset(agents_asset(root, subs, mode), label))
        if new != old:
            actions.append({"kind": "file", "target": agents.name, "detail": "upsert agent guidance block"})
            if not args.dry_run:
                agents.write_text(new)
        if args.dry_run and not agents.exists():
            actions.append({"kind": "file", "target": agents.name, "detail": "upsert repo map"})
        else:
            update_repo_map(root, subs, args.dry_run, actions)

    if not args.no_justfile:
        jf = find_justfile(root) or root / "justfile"
        old = jf.read_text() if jf.exists() else ""
        new = upsert_block(old, JUST_BEGIN, JUST_END, render_asset("justfile.snippet", label))
        if new != old:
            actions.append({"kind": "file", "target": jf.name, "detail": "upsert sub-* recipes"})
            if not args.dry_run:
                jf.write_text(new)

    if not args.no_gitignore and ensure_gitignore(root, args.dry_run, wt_root):
        actions.append({"kind": "file", "target": ".gitignore", "detail": f"ignore {worktree_root_rel(root, wt_root)}/"})

    if getattr(args, "with_ci", False):
        wf = root / ".github" / "workflows" / "superproject-bump.yml"
        content = render_asset("superproject-bump.yml")
        if not wf.exists() or wf.read_text() != content:
            actions.append({"kind": "file", "target": str(wf.relative_to(root)), "detail": "scheduled bump workflow"})
            if not args.dry_run:
                wf.parent.mkdir(parents=True, exist_ok=True)
                wf.write_text(content)

    if getattr(args, "with_hook", False):
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

    # Submodule display/push settings mean nothing to a pointer-only home repo.
    pointer_only = ((mode or marker_get(root, "workspace.mode")) == "pointer"
                    and not any(s.kind == "submodule" for s in subs))
    if not args.no_git_config and not pointer_only:
        for key, value in (("diff.submodule", "log"), ("status.submoduleSummary", "true"),
                           ("push.recurseSubmodules", "check")):
            if not git("config", "--local", "--get", key, cwd=root, check=False):
                actions.append({"kind": "git-config", "target": key, "detail": value})
                if not args.dry_run:
                    git("config", "--local", key, value, cwd=root)


def cmd_adopt(root: Path, subs: list[Sub], args) -> int:
    actions: list[dict] = []
    overrides: dict[str, tuple[str, str | None]] = {}
    for spec in args.set or []:
        ident, _, val = spec.partition("=")
        pol, _, bump = val.partition(":")
        if pol not in POLICIES or (bump and bump not in BUMP_MODES):
            raise UsageError(f"--set {spec!r}: expected NAME=track|pin|lazy[:pr|direct|manual]")
        target = resolve(subs, ident)
        if target.kind == "pointer":
            raise UsageError(f"--set {spec!r}: {target.name} is a pointer child; pointers have no policy")
        overrides[target.name] = (pol, bump or None)

    def set_key(s: Sub, key: str, value: str) -> None:
        actions.append({"kind": "gitmodules", "target": f"submodule.{s.name}.{key}", "detail": value})
        if not args.dry_run:
            git("config", "-f", ".gitmodules", f"submodule.{s.name}.{key}", value, cwd=root)

    for s in subs:
        if s.kind == "pointer":
            continue
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
                                  cwd=child_dir(root, s), check=False).removeprefix("origin/")
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

    scaffold(root, args, actions, subs=subs if args.dry_run else load_subs(root))

    verb = "would" if args.dry_run else "did"
    text = "\n".join(f"{verb}: {a['kind']:10} {a['target']} = {a['detail']}" for a in actions) or "already adopted; nothing to do"
    if actions and not args.dry_run:
        text += "\nreview with `git diff`, then run `audit`"
    emit(args, {"actions": actions, "dry_run": args.dry_run}, text)
    return 0


# ---------------------------------------------------------------- new / add

def report_actions(args, actions: list[dict]) -> str:
    verb = "would" if args.dry_run else "did"
    return "\n".join(f"{verb}: {a['kind']:10} {a['target']}" + (f" = {a['detail']}" if a["detail"] else "")
                     for a in actions)


def cmd_new(_root: Path | None, _subs: list[Sub], args) -> int:
    d = Path(args.dir).expanduser().resolve()
    if d.exists() and not d.is_dir():
        raise UsageError(f"{d} exists and is not a directory")
    if is_workspace_root(d):
        raise Refused(f"{d} is already a workspace root; use `adopt` to refresh its scaffolding")
    top = git("rev-parse", "--show-toplevel", cwd=d, check=False)
    if not top and not d.exists():
        # The directory will be created: make sure no ancestor is a work tree.
        anc = next((a for a in d.parents if a.is_dir()), None)
        top = git("rev-parse", "--show-toplevel", cwd=anc, check=False) if anc else ""
    if top and Path(top).resolve() != d:
        raise Refused(f"{d} is inside another repository's work tree ({Path(top).resolve()}); "
                      "a workspace root must be its own repository. Pick a directory outside it, "
                      "or run `adopt` in that repository instead")
    wt_root = None
    if args.worktree_root:
        p = Path(args.worktree_root).expanduser()
        wt_root = p if p.is_absolute() else d / p

    actions: list[dict] = []
    if not top:
        actions.append({"kind": "git", "target": str(d), "detail": "git init"})
        if not args.dry_run:
            d.mkdir(parents=True, exist_ok=True)
            git("init", "-q", cwd=d)
    settings = [("workspace.mode", args.mode)]
    if args.worktree_root:
        settings.append(("workspace.worktree-root", args.worktree_root))
    for key, value in settings:
        actions.append({"kind": "marker", "target": f"{MARKER} {key}", "detail": value})
        if not args.dry_run:
            git("config", "-f", MARKER, key, value, cwd=d)
    scaffold(d, args, actions, wt_root, mode=args.mode)

    text = report_actions(args, actions)
    if not args.dry_run:
        text += ("\nnothing was committed; next: `add URL [PATH]` for each child, "
                 "review with `git status`, then commit")
    emit(args, {"root": str(d), "mode": args.mode, "actions": actions, "dry_run": args.dry_run}, text)
    return 0


def url_basename(url: str) -> str:
    base = re.split(r"[/:\\]", url.rstrip("/"))[-1]
    return base.removesuffix(".git")


def path_ignored(root: Path, rel: str) -> bool:
    return git_rc("check-ignore", "-q", "--no-index", f"{rel}/probe", cwd=root) == 0


def cmd_add(root: Path, subs: list[Sub], args) -> int:
    mode = marker_get(root, "workspace.mode") or "submodule"
    if mode not in MODES:
        raise UsageError(f"workspace.mode = {mode!r} in {MARKER}; expected {'|'.join(MODES)}")
    kind = "pointer" if args.pointer else "submodule" if args.submodule else mode
    if kind == "pointer":
        bad = [f for f, v in (("--policy", args.policy), ("--bump", args.bump), ("--ref", args.ref)) if v]
        if bad:
            raise UsageError(f"{', '.join(bad)} apply to submodule children only; a pointer has no gitlink")
    else:
        if args.no_clone:
            raise UsageError("--no-clone applies to pointer children only (git submodule add always clones)")
        args.policy = args.policy or "pin"
        if args.bump and args.policy != "track":
            raise UsageError("--bump applies only to --policy track")
    base_name = url_basename(args.url)
    if kind == "pointer":
        name = args.name or base_name
        raw = args.path or (f"repos/{name}" if name else "")
    else:
        raw = args.path or base_name
        name = None
    if not raw:
        raise UsageError(f"cannot derive a path from {args.url!r}; pass PATH")
    absolute = Path(raw).expanduser().is_absolute() or raw.startswith("~")
    if kind == "submodule" and absolute:
        raise UsageError(f"submodule path {raw!r} must be relative to the workspace root")
    path = raw.rstrip("/") if absolute else Path(os.path.normpath(raw)).as_posix()
    if path == "." or (kind == "submodule" and path.startswith("../")):
        raise UsageError(f"submodule path {raw!r} must stay inside the workspace root")
    name = name or args.name or path
    new = Sub(name=name, path=path, url=args.url, branch=args.branch, policy=args.policy,
              bump=args.bump, tier=args.tier, update=None, kind=kind, role=args.role)
    if wt_key(new).split("/")[0] == TASKS_DIR:
        raise Refused(f"{TASKS_DIR!r} is reserved under the worktree root; choose another {'name' if kind == 'pointer' else 'path'}")
    target = child_dir(root, new)
    for s in subs:
        taken = {s.name, s.path, wt_key(s)}
        if taken & {new.name, new.path, wt_key(new)} or child_dir(root, s).resolve() == target.resolve():
            raise Refused(f"{name!r} ({path}) collides with existing child {s.name!r} ({s.path})")
    inside = target.resolve().is_relative_to(root.resolve())
    adopt_clone = False
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        if kind == "pointer" and checkout_state(root, new) == "ok":
            origin = git("remote", "get-url", "origin", cwd=target, check=False)
            if origin != args.url:
                raise Refused(f"{path} is a clone of {origin or '(no origin)'}, not {args.url}; "
                              "pass the matching URL or another PATH")
            adopt_clone = True
        else:
            hint = (" Adopting an existing embedded repository as a submodule is not supported here; see "
                    "`git submodule add` on an existing repo and `git submodule absorbgitdirs`."
                    if kind == "submodule" and os.path.lexists(target / ".git") else "")
            raise Refused(f"{path} exists and is not empty; refusing to add a child over it.{hint}")
    if not git_dirs(root):
        raise Refused(f"{root} is not a git repository; run `new` first")
    if kind == "submodule" or inside:
        assert_durable_store(root)
    if kind == "submodule" and (root / ".gitmodules").exists() \
            and git_rc("diff", "--quiet", "--", ".gitmodules", cwd=root) != 0:
        raise Refused(".gitmodules has unstaged changes; stage or discard them first")

    actions: list[dict] = []
    cfg_file, section = (".gitmodules", "submodule") if kind == "submodule" else (MARKER, "repo")

    def run(*cmd: str, cwd: Path = root) -> None:
        where = "" if cwd == root else f" (in {display_path(root, cwd)})"
        actions.append({"kind": "git", "target": "git " + " ".join(cmd) + where, "detail": ""})
        if not args.dry_run:
            git(*cmd, cwd=cwd)

    def set_key(key: str, value: str) -> None:
        actions.append({"kind": cfg_file.lstrip("."), "target": f"{section}.{name}.{key}", "detail": value})
        if not args.dry_run:
            git("config", "-f", cfg_file, f"{section}.{name}.{key}", value, cwd=root)

    if kind == "submodule":
        run("submodule", "add", "-q", *(["--name", name] if args.name else []),
            *(["-b", args.branch] if args.branch else []), "--", args.url, path)
        set_key("x-policy", args.policy)
        if args.policy == "track":
            set_key("x-bump", args.bump or "manual")
    else:
        set_key("path", path)
        set_key("url", args.url)
        if args.branch:
            set_key("branch", args.branch)
        if adopt_clone:
            actions.append({"kind": "adopt", "target": path, "detail": "existing clone with matching origin"})
        elif not args.no_clone:
            if not args.dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
            run("clone", "-q", *(["--branch", args.branch] if args.branch else []), "--", args.url, str(target))
    if args.tier:
        set_key("x-tier", args.tier)
    if args.role:
        set_key("x-role", args.role)
    if kind == "submodule" and args.policy == "lazy":
        set_key("update", "none")
    branch = args.branch
    cloned = kind == "submodule" or adopt_clone or not args.no_clone
    if not branch and cloned and (kind == "pointer" or args.policy != "lazy"):
        if args.dry_run:
            actions.append({"kind": cfg_file.lstrip("."), "target": f"{section}.{name}.branch",
                            "detail": "(the child's origin/HEAD after cloning)"})
        else:
            head = git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", cwd=target, check=False)
            branch = head.removeprefix("origin/") if head.startswith("origin/") else \
                git("symbolic-ref", "-q", "--short", "HEAD", cwd=target, check=False)
            if branch:
                set_key("branch", branch)
    if kind == "submodule":
        if args.ref:
            run("checkout", "-q", "--detach", args.ref, cwd=target)
            run("add", "--", path)
        run("add", "--", ".gitmodules")
    elif inside and not path_ignored(root, display_path(root, target)):
        rel = display_path(root, target)
        actions.append({"kind": "file", "target": ".gitignore", "detail": f"ignore /{rel}/"})
        if not args.dry_run:
            gi = root / ".gitignore"
            text = gi.read_text() if gi.exists() else ""
            sep = "" if not text or text.endswith("\n") else "\n"
            gi.write_text(f"{text}{sep}# superproject-workspace: pointer clone\n/{rel}/\n")
    if args.dry_run:
        actions.append({"kind": "file", "target": "repo map", "detail": "refresh (if an agents file exists)"})
    else:
        update_repo_map(root, load_subs(root), False, actions, create=False)

    staged = None if args.dry_run or kind == "pointer" else index_gitlink(root, path)
    data = {"root": str(root), "name": name, "path": path, "kind": kind, "policy": args.policy if kind == "submodule" else None,
            "branch": branch, "gitlink": staged, "cloned": bool(cloned and not args.dry_run),
            "actions": actions, "dry_run": args.dry_run}
    text = report_actions(args, actions)
    if not args.dry_run:
        text += (f"\nstaged {path} at {short(staged)} and .gitmodules; nothing was committed. "
                 "Review with `git diff --cached`, then commit" if kind == "submodule" else
                 f"\nwrote {MARKER}; nothing was staged or committed. Review with `git status`, then commit")
    emit(args, data, text)
    return 0


# ---------------------------------------------------------------- ci-plan

def cmd_ci_plan(root: Path, subs: list[Sub], args) -> int:
    if args.only:
        hit = next((s for s in subs if s.kind == "pointer" and args.only in (s.name, s.path)), None)
        if hit:
            raise Refused(f"{hit.name} {POINTER_NO_GITLINK}")
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
    sel.add_argument("--kind", choices=KINDS, help="only children of this kind")

    dry = argparse.ArgumentParser(add_help=False)
    dry.add_argument("--dry-run", action="store_true", help="report what would change; change nothing")

    ap = argparse.ArgumentParser(
        prog="superproject.py",
        description="Keep a multi-repo workspace on track: a git-submodule superproject (policy-driven status,\n"
                    "bump, preflight) or a pointer-only home repo, with child/task worktrees, repair, and audit.",
        epilog="Policy lives in .gitmodules: x-policy=track|pin|lazy, x-bump=pr|direct|manual, x-tier=<group>.\n"
               f"The root is found from --root, $SUPERPROJECT_ROOT, or the cwd (a dir with .gitmodules or {MARKER}).\n"
               "Exit codes: 0 ok, 1 refused or check failed, 2 usage error.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser(
        "new", parents=[common, dry], help="create a workspace root (git init if needed, marker, scaffolding)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"Create a workspace root in DIR: `git init` unless DIR is already a repository root,\n"
                    f"write {MARKER} ([workspace] mode, worktree-root), then the same scaffolding as\n"
                    "`adopt` (AGENTS.md block, justfile recipes, .gitignore entry, local git config).\n"
                    "Never commits.",
        epilog="Refuses (exit 1) when DIR is inside another repository's work tree or is already a workspace\n"
               "root (use `adopt` there). --root is ignored.\n\n"
               "Examples:\n"
               "  superproject.py new my-workspace --dry-run\n"
               "  superproject.py new . --worktree-root .worktrees\n\n"
               "Exit codes: 0 ok, 1 refused, 2 usage error.",
    )
    p.add_argument("dir", nargs="?", default=".", metavar="DIR", help="directory to turn into a root (default: cwd)")
    p.add_argument("--mode", choices=MODES, default="submodule",
                   help="default kind of child for `add`: submodule (recommended) or pointer (default: submodule)")
    p.add_argument("--worktree-root", metavar="PATH",
                   help=f"where child worktrees go: relative to DIR, absolute, or ~ (default: {WORKTREE_DIR})")
    p.add_argument("--no-agents", action="store_true", help="skip the AGENTS.md guidance block")
    p.add_argument("--no-justfile", action="store_true", help="skip the justfile sub-* recipes")
    p.add_argument("--no-gitignore", action="store_true", help="skip ignoring the worktree root")
    p.add_argument("--no-git-config", action="store_true",
                   help="skip local diff.submodule/status.submoduleSummary/push.recurseSubmodules")
    p.set_defaults(func=cmd_new, needs_root=False)

    p = sp.add_parser(
        "add", parents=[common, dry], help="add a child (submodule or pointer) with its metadata (no commit)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Add a child repository. The kind defaults to workspace.mode in .superproject.\n\n"
                    "submodule: `git submodule add`, write x-policy/x-bump/x-tier/x-role (and update=none\n"
                    "  for lazy) to .gitmodules, record `branch` from the child's origin/HEAD unless given or\n"
                    "  lazy, optionally detach at --ref, then stage the child and .gitmodules. A relative URL\n"
                    "  (./x, ../x) is resolved by git against the superproject's own remote.\n"
                    f"pointer: write [repo \"NAME\"] (path, url, branch, x-tier, x-role) to {MARKER} and clone\n"
                    "  it (unless --no-clone). An existing clone at PATH whose origin matches URL is adopted\n"
                    "  in place. A PATH inside the root is gitignored. PATH may be ../x, ~/x or absolute.\n\n"
                    "Both refresh the repo map in the agents file when one exists. Never commits.",
        epilog="Defaults: submodule PATH = URL basename without .git, NAME = PATH;\n"
               "pointer NAME = URL basename, PATH = repos/NAME.\n"
               "Refuses (exit 1) when NAME/PATH collide with an existing child, the target exists and is not\n"
               "empty (or is a clone of another URL), .gitmodules has unstaged changes, the root is a linked\n"
               f"worktree (for a target inside it), or the worktree key starts with {TASKS_DIR}.\n\n"
               "Examples:\n"
               "  superproject.py add https://example.com/org/app.git --policy track --bump pr\n"
               "  superproject.py add https://example.com/org/lib.git libs/lib --name lib --ref v1.2.0\n"
               "  superproject.py add https://example.com/org/ref.git refs/ref --policy lazy --tier reference\n"
               "  superproject.py add https://example.com/org/docs.git --pointer --role 'Public docs site'\n"
               "  superproject.py add https://example.com/org/infra.git ../infra --pointer --no-clone\n\n"
               "Exit codes: 0 ok, 1 refused, 2 usage error.",
    )
    p.add_argument("url", metavar="URL", help="clone URL of the child")
    p.add_argument("path", nargs="?", metavar="PATH",
                   help="checkout path (submodule: relative, default URL basename; pointer: default repos/NAME)")
    p.add_argument("--name", help="child name (submodule default: PATH; pointer default: URL basename)")
    kind = p.add_mutually_exclusive_group()
    kind.add_argument("--submodule", action="store_true", help="add as a git submodule (pinned by a gitlink)")
    kind.add_argument("--pointer", action="store_true",
                      help=f"add as a pointer: a [repo] entry in {MARKER} plus a plain clone, no gitlink")
    p.add_argument("--no-clone", action="store_true", help="pointer only: record it now, clone later with `init NAME`")
    p.add_argument("--policy", choices=POLICIES, help="submodule only: x-policy (default: pin)")
    p.add_argument("--bump", choices=BUMP_MODES, help="x-bump for --policy track (default: manual)")
    p.add_argument("--tier", help="x-tier grouping")
    p.add_argument("--branch", help="tracking branch (default: the child's origin/HEAD; unset for lazy)")
    p.add_argument("--role", help="x-role: one-line purpose of the child")
    p.add_argument("--ref", metavar="REV", help="record this child revision instead of its default branch tip")
    p.set_defaults(func=cmd_add)

    p = sp.add_parser("status", parents=[common, sel], help="policy, lag and drift for every child")
    p.add_argument("--fetch", action="store_true", help="fetch each child's origin first")
    p.set_defaults(func=cmd_status)

    p = sp.add_parser("init", parents=[common, sel, dry],
                      help="initialize children (lazy ones only when named, by --tier, or with --all)")
    p.add_argument("--all", action="store_true", help="include lazy children")
    p.add_argument("--recursive", action="store_true",
                   help="also initialize nested submodules of the children this call initializes")
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

    p = sp.add_parser("worktree", parents=[common],
                      help="single-child worktrees under the worktree root (default .worktrees/<path>/<branch>)")
    wsp = p.add_subparsers(dest="wt_cmd", required=True)
    w = wsp.add_parser("add", parents=[common, dry], help="create a child worktree on a branch")
    w.add_argument("submodule")
    w.add_argument("branch")
    w.add_argument("--base", help="start point for a new branch (default: origin/<branch> for track, gitlink otherwise)")
    w.add_argument("--no-fetch", action="store_true")
    w = wsp.add_parser("list", parents=[common], help="list child worktrees (with their TASK) and whether they are merged")
    w.add_argument("--all", action="store_true", help="also list worktrees outside the worktree root")
    w = wsp.add_parser("remove", parents=[common, dry], help="remove a child worktree")
    w.add_argument("submodule")
    w.add_argument("branch")
    w.add_argument("--delete-branch", action="store_true", help="also delete the branch (safe delete unless --force)")
    w.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_worktree)

    p = sp.add_parser(
        "task", parents=[common], help="one task across several children: <worktree-root>/_tasks/<task>/<child>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="A task is a set of child worktrees on the same branch, laid out as\n"
                    "<worktree-root>/_tasks/<task>/<child-path>, mirroring the superproject so relative paths\n"
                    "between members still resolve. Membership is read from each child's `git worktree list`;\n"
                    "there is no state file.",
        epilog="Examples:\n"
               "  superproject.py task open login app lib\n"
               "  superproject.py task open login api --base api=v2.1.0      # add a member later\n"
               "  superproject.py task list login --json\n"
               "  superproject.py task close login --delete-branch\n\n"
               "Exit codes: 0 ok, 1 refused (nothing changed, or open rolled back), 2 usage error.",
    )
    tsp = p.add_subparsers(dest="task_cmd", required=True)
    w = tsp.add_parser("open", parents=[common, dry], help="create (or extend) a task's member worktrees",
                       description="Check every member first (initialized, durable store, target free, branch not\n"
                                   "checked out elsewhere); then create them. If one creation fails, the worktrees\n"
                                   "and branches this call created are removed again. Existing members are\n"
                                   "reported as `exists`, so rerunning is safe.",
                       formatter_class=argparse.RawDescriptionHelpFormatter)
    w.add_argument("task", metavar="TASK", help="task name; must be a valid branch name")
    w.add_argument("children", nargs="+", metavar="CHILD", help="child name, path, or basename")
    w.add_argument("--branch", help="branch in every member (default: TASK)")
    w.add_argument("--base", action="append", metavar="CHILD=REV",
                   help="start point for one member's new branch (default: origin/<branch> for track, gitlink otherwise)")
    w.add_argument("--no-fetch", action="store_true")
    w = tsp.add_parser("list", parents=[common], help="members with dirty/untracked/unpushed/merged state")
    w.add_argument("task", nargs="?", metavar="TASK", help="only this task")
    w = tsp.add_parser("close", parents=[common, dry], help="remove a task's worktrees (all-or-nothing checks)",
                       description="Refuses the whole close when any selected member has modified or untracked\n"
                                   "files, or, with --delete-branch, an unmerged branch (unless --force). Then\n"
                                   "`git worktree remove` each member, optionally delete its branch, and rmdir\n"
                                   "empty parents up to the worktree root. Never deletes a directory tree itself.",
                       formatter_class=argparse.RawDescriptionHelpFormatter)
    w.add_argument("task", metavar="TASK")
    w.add_argument("children", nargs="*", metavar="CHILD", help="close only these members")
    w.add_argument("--delete-branch", action="store_true", help="also delete each member's branch")
    w.add_argument("--force", action="store_true", help="discard modified/untracked files and unmerged branches")
    p.set_defaults(func=cmd_task)

    p = sp.add_parser(
        "repair", parents=[common, dry], help="fix severed child worktrees and stale submodule state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Scan child worktrees and stores, then fix what the flags allow:\n"
                    "  (no flag)          relink worktrees whose store moved (git worktree repair); lossless\n"
                    "  --prune            git worktree prune, and drop .git/config sections of undeclared submodules\n"
                    "  --reattach         give orphaned worktrees a new admin dir in the child's own store,\n"
                    "                     on branch rescue/<dir> at --base (default: gitlink); files are kept\n"
                    "  --delete-orphans   delete the orphan directories named as PATH (the only deleting step)\n"
                    "Never deletes a .git/modules store, force-removes a dirty worktree, moves worktrees, or\n"
                    "touches worktree-at-risk entries; those get manual steps.",
        epilog="PATH limits --reattach/--delete-orphans (and relinking) to those directories.\n\n"
               "Examples:\n"
               "  superproject.py repair --dry-run\n"
               "  superproject.py repair --reattach .worktrees/app/feat\n"
               "  superproject.py repair --delete-orphans .worktrees/app/old --dry-run\n\n"
               "Exit codes: 0 ok, 1 an action failed or error-level findings remain, 2 usage error.",
    )
    p.add_argument("paths", nargs="*", metavar="PATH", help="restrict actions to these directories")
    p.add_argument("--prune", action="store_true", help="prune stale worktree entries and stale submodule config")
    p.add_argument("--reattach", action="store_true", help="reattach orphaned worktrees to the child's store")
    p.add_argument("--base", metavar="REV", help="start point of the rescue branch for --reattach")
    p.add_argument("--delete-orphans", action="store_true", help="delete the orphan directories given as PATH")
    p.set_defaults(func=cmd_repair)

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
        if not getattr(args, "needs_root", True):
            return args.func(None, [], args)
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
