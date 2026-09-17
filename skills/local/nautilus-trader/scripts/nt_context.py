#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Detect the NautilusTrader generation of a project and sync version-matched docs.

doctor: inspect an interpreter, project pins, Cargo crates and v1/v2-only names,
        then recommend a generation, version and documentation git ref.
docs:   materialize docs/, examples/ and root guides for one git tag or branch
        into an XDG cache through a sparse partial clone (git only, no token).

No NautilusTrader import is needed in this helper's own environment.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.request
import uuid

REPO_URL = "https://github.com/nautechsystems/nautilus_trader.git"
PYPI_URL = "https://pypi.org/pypi/nautilus_trader/json"
CACHE_NAME = "nautilus-trader-agent"
TTL = 24 * 60 * 60
SCHEMA = 1
SPARSE = ("/docs/**/*.md", "/docs/**/*.py", "/docs/**/*.rs", "/examples/", "/MIGRATION_V2.md", "/RELEASES.md", "/ADAPTERS.md", "/ROADMAP.md")
ROOT_FILES = ("MIGRATION_V2.md", "RELEASES.md", "ADAPTERS.md", "ROADMAP.md")
VERIFIED_AGAINST = "nautilus_trader 1.231.0 and 2.0.0rc5 on 2026-09-17"
WHEEL_PYTHON = (3, 12), (3, 15)  # current wheels: >=3.12,<3.15
# Names that exist in only one generation. Heuristic: re-check against MIGRATION_V2.md.
MARKERS = {
    "v1": {"TradingNode", "TradingNodeConfig", "ActorConfig", "ExecAlgorithmConfig", "ExecEngineConfig",
           "LoggingConfig", "on_quote_tick", "on_trade_tick", "on_order_book_deltas", "subscribe_quote_ticks",
           "subscribe_trade_ticks", "subscribe_order_book_deltas", "request_quote_ticks", "request_trade_ticks",
           "nautilus_trader.backtest.node", "nautilus_trader.backtest.engine", "nautilus_trader.live.node",
           "nautilus_trader.model.enums", "nautilus_trader.model.identifiers", "nautilus_trader.core.nautilus_pyo3",
           "nautilus_trader.test_kit"},
    "v2": {"LiveNode", "LiveNodeConfig", "DataActorConfig", "ExecutionAlgorithmConfig", "ExecutionEngineConfig",
           "LoggerConfig", "on_quote", "on_trade", "on_book_deltas", "subscribe_quotes", "subscribe_trades",
           "subscribe_book_deltas", "request_quotes", "request_trades", "add_simulated_exec_client",
           "nautilus_trader.testkit"},
}
SKIPPED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "site", "target", "build", "dist"}
VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?(?:\.dev(\d+))?(?:\+[\w.]+)?")


class ContextError(Exception):
    def __init__(self, message: str, code: int = 3):
        super().__init__(message)
        self.code = code


def log(message: str) -> None:
    print(message, file=sys.stderr)


def absolute(path: str | Path) -> Path:
    # Do not resolve the final symlink: resolving .venv/bin/python loses the venv.
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def cache_root(override: str | Path | None = None) -> Path:
    if override is not None:
        return absolute(override)
    xdg = os.environ.get("XDG_CACHE_HOME", "")
    if xdg and Path(xdg).is_absolute():
        return Path(xdg) / CACHE_NAME
    if xdg:
        log(f"Ignoring relative XDG_CACHE_HOME; using ~/.cache/{CACHE_NAME}.")
    return Path.home() / ".cache" / CACHE_NAME


def run(args: list[str], *, cwd: Path | None = None, timeout: float = 120, label: str | None = None) -> subprocess.CompletedProcess:
    label = label or Path(args[0]).name
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContextError(f"Cannot run {label}: {type(exc).__name__}. Check the executable and connection.") from exc
    if result.returncode:
        detail = result.stderr.decode(errors="replace").strip().splitlines()
        hint = detail[-1][:200] if detail else f"exit {result.returncode}"
        raise ContextError(f"{label} failed: {hint}")
    return result


# ---------------------------------------------------------------- versions

def parse_version(value: str | None) -> dict | None:
    match = VERSION.fullmatch(value.strip()) if value else None
    if not match:
        return None
    major, minor, patch, phase, number, dev = match.groups()
    nightly = phase == "a" and number is not None and len(number) >= 8  # aYYYYMMDD nightly builds
    return {"major": int(major), "key": (int(major), int(minor), int(patch), {"a": 0, "b": 1, "rc": 2, None: 3}[phase], int(number or 0)),
            "prerelease": phase is not None, "dev": dev is not None or nightly}


def generation_of(version: str | None) -> str | None:
    parsed = parse_version(version)
    return {1: "v1", 2: "v2"}.get(parsed["major"]) if parsed else None


def ref_for_version(version: str) -> tuple[str | None, bool]:
    """Return (git ref, approximate). Dev builds map to their moving branch."""
    parsed = parse_version(version)
    if not parsed:
        return None, True
    if parsed["dev"]:
        return ("develop_v1" if parsed["major"] == 1 else "develop"), True
    return "v" + VERSION.fullmatch(version.strip()).group(0).split(".dev")[0].split("+")[0], False


def pypi_status(offline: bool) -> dict:
    if offline:
        return {"status": "skipped", "reason": "offline"}
    url = os.environ.get("NAUTILUS_AGENT_PYPI_URL", PYPI_URL)
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            releases = json.load(response)["releases"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"status": "unknown", "reason": f"PyPI metadata unavailable ({type(exc).__name__})"}
    versions = []
    for name, files in releases.items():
        parsed = parse_version(name)
        if parsed and not parsed["dev"] and files and not all(f.get("yanked") for f in files):
            versions.append((parsed["key"], name, parsed))
    stable = max((v for v in versions if not v[2]["prerelease"]), default=None)
    pre = max((v for v in versions if v[2]["prerelease"]), default=None)
    newer_pre = pre if pre and (not stable or pre[0] > stable[0]) else None
    by_generation = {}
    for label, major in (("v1", 1), ("v2", 2)):
        same = [v for v in versions if v[2]["major"] == major]
        final = [v for v in same if not v[2]["prerelease"]]
        best = max(final or same, default=None)
        by_generation[label] = best[1] if best else None
    return {"status": "ok", "stable": stable[1] if stable else None, "prerelease": newer_pre[1] if newer_pre else None,
            "pre_flag_required": bool(newer_pre and stable and newer_pre[2]["major"] > stable[2]["major"]),
            "latest_by_generation": by_generation}


# ---------------------------------------------------------------- environment

def python_path(project: Path, explicit: str | None) -> Path:
    if explicit:
        found = shutil.which(explicit) if os.sep not in explicit else explicit
        if not found or not Path(found).exists():
            raise ContextError("Python executable not found; pass --python /absolute/path/to/python.", 2)
        return absolute(found)
    for candidate in (project / ".venv/bin/python", project / ".venv/Scripts/python.exe"):
        if candidate.exists():
            return absolute(candidate)
    return absolute(sys.executable)


PROBE = r'''
import contextlib, importlib, importlib.metadata, importlib.util, io, json, os, sys
out = {"python": sys.executable, "python_version": sys.version.split()[0]}
item = {"installed": False, "importable": False, "native_core": None}
try:
    item["distribution_version"] = importlib.metadata.version("nautilus_trader")
    item["installed"] = True
except importlib.metadata.PackageNotFoundError:
    pass
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        spec = importlib.util.find_spec("nautilus_trader")
        if spec is not None:
            item["origin"] = spec.origin
            names = []
            for base in spec.submodule_search_locations or []:
                for sub in ("", "core"):
                    try:
                        names += [os.path.join(sub, x) for x in os.listdir(os.path.join(base, sub))]
                    except OSError:
                        pass
            if any(os.path.basename(n).startswith("_libnautilus") for n in names):
                item["native_core"] = "pyo3"
            elif any(n.startswith(os.path.join("core", "nautilus_pyo3")) or n.endswith((".pyx", ".pxd")) for n in names):
                item["native_core"] = "cython"
            module = importlib.import_module("nautilus_trader")
            item["version"] = str(getattr(module, "__version__", ""))
            item["importable"] = True
except Exception as exc:
    item["import_error"] = type(exc).__name__
out["package"] = item
print(json.dumps(out))
'''


def probe_python(python: Path, project: Path) -> dict:
    try:
        result = json.loads(run([str(python), "-c", PROBE], cwd=project, label="interpreter probe").stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ContextError("Interpreter probe did not return JSON; inspect the target Python environment.") from exc
    package = result["package"]
    version = package.get("version") or package.get("distribution_version")
    package["generation"] = generation_of(version)
    parts = tuple(int(x) for x in result["python_version"].split(".")[:2])
    result["python_supported_by_current_wheels"] = WHEEL_PYTHON[0] <= parts < WHEEL_PYTHON[1]
    return result


# ---------------------------------------------------------------- project evidence

NAME = re.compile(r"nautilus[-_.]trader", re.I)


def spec_pin(source: str, spec: str) -> dict:
    spec = spec.strip()
    exact = re.fullmatch(r"={2,3}\s*([^\s,;]+)", spec)
    if exact and parse_version(exact[1]):
        return {"source": source, "spec": spec, "version": exact[1], "exact": True, "generation": generation_of(exact[1])}
    # Ranges and wildcards only suggest a generation: take the lower bound, or <2 / <2.0.
    lower = re.search(r"(?:>=|~=|>|\^|~|={2,3})\s*(\d+)", spec)
    upper = re.search(r"<=?\s*(\d+)(?:\.(\d+))?", spec)
    if lower:
        generation = {"1": "v1", "2": "v2"}.get(lower[1])
    else:
        generation = "v1" if upper and upper[1] == "2" and upper[2] in (None, "0") else None
    return {"source": source, "spec": spec or "*", "version": None, "exact": False, "generation": generation}


def read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContextError(f"Cannot parse {path.name}; repair it or pass another --project.", 2) from exc


def requirement_pin(source: str, line: str) -> dict | None:
    match = re.match(r"\s*nautilus[-_.]trader(?![\w.-])\s*(?:\[[^\]]*\])?\s*([^;#]*)", line, re.I)
    return spec_pin(source, match[1]) if match else None


def pins_and_crates(project: Path) -> tuple[list[dict], list[dict], str | None]:
    pins: list[dict] = []
    crates: list[dict] = []
    prerelease = None
    for lock in ("uv.lock", "poetry.lock", "pdm.lock"):
        path = project / lock
        if path.is_file():
            for package in read_toml(path).get("package", []):
                if NAME.fullmatch(str(package.get("name", ""))) and package.get("version"):
                    pins.append({**spec_pin(lock, "==" + package["version"]), "locked": True})
    pyproject = project / "pyproject.toml"
    if pyproject.is_file():
        config = read_toml(pyproject)
        project_table = config.get("project", {})
        groups = [project_table.get("dependencies", [])] + list(project_table.get("optional-dependencies", {}).values())
        groups += [x for x in config.get("dependency-groups", {}).values() if isinstance(x, list)]
        for group in groups:
            for requirement in group:
                if isinstance(requirement, str) and (pin := requirement_pin("pyproject.toml", requirement)):
                    pins.append(pin)
        for key, value in config.get("tool", {}).get("poetry", {}).get("dependencies", {}).items():
            if NAME.fullmatch(key):
                spec = value if isinstance(value, str) else str(value.get("version", "")) if isinstance(value, dict) else ""
                # Poetry reads a bare version as a caret range, not an exact pin.
                pins.append(spec_pin("pyproject.toml [tool.poetry]", spec if not spec or re.match(r"\s*[<>=~^!*]", spec) else "^" + spec))
        prerelease = config.get("tool", {}).get("uv", {}).get("prerelease")
    for path in sorted(project.glob("requirements*.txt")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if pin := requirement_pin(path.name, line):
                pins.append(pin)
    cargo_lock = project / "Cargo.lock"
    if cargo_lock.is_file():
        for package in read_toml(cargo_lock).get("package", []):
            if str(package.get("name", "")).startswith("nautilus-"):
                crates.append({"source": "Cargo.lock", "name": package["name"], "version": package.get("version"), "git": package.get("source", "").startswith("git+")})
    cargo = project / "Cargo.toml"
    if cargo.is_file():
        config = read_toml(cargo)
        tables = [config.get(k, {}) for k in ("dependencies", "dev-dependencies")] + [config.get("workspace", {}).get("dependencies", {})]
        for table in tables:
            for name, value in table.items():
                if name.startswith("nautilus-"):
                    detail = value if isinstance(value, dict) else {"version": value}
                    crates.append({"source": "Cargo.toml", "name": name, "version": detail.get("version"),
                                   "git": detail.get("git"), "branch": detail.get("branch"), "rev": detail.get("rev")})
    # Locks first so the most precise pin wins when choosing a version.
    pins.sort(key=lambda p: (not p.get("locked"), not p["exact"]))
    return pins, crates, prerelease


def code_names(tree: ast.AST) -> tuple[bool, list[tuple[str, int]]]:
    uses_package = False
    names: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                uses_package |= alias.name.split(".")[0] == "nautilus_trader"
                names.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.module:
            uses_package |= node.module.split(".")[0] == "nautilus_trader"
            names.append((node.module, node.lineno))
            names.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append((node.name, node.lineno))
        elif isinstance(node, ast.Attribute):
            names.append((node.attr, node.lineno))
        elif isinstance(node, ast.Name):
            names.append((node.id, node.lineno))
    return uses_package, names


def marker_scan(project: Path, limit: int = 300, samples: int = 20) -> dict:
    found: dict[str, list[dict]] = {"v1": [], "v2": []}
    counts = {"v1": 0, "v2": 0}
    files = []
    count = 0
    truncated = False
    for directory, children, names in os.walk(project):
        children[:] = sorted(x for x in children if x not in SKIPPED_DIRS and not x.startswith("."))
        for name in sorted(names):
            if not name.endswith(".py"):
                continue
            count += 1
            if count > limit:
                truncated = True
                break
            path = Path(directory) / name
            try:
                if path.stat().st_size > 1_000_000:
                    continue
                uses_package, used = code_names(ast.parse(path.read_text(encoding="utf-8")))
            except (OSError, UnicodeError, SyntaxError, ValueError):
                continue
            if not uses_package:
                continue  # generic names such as on_quote only count next to a nautilus_trader import
            relative = str(path.relative_to(project))
            files.append(relative)
            seen = set()
            for identifier, line in used:
                if "." in identifier:  # module paths also match their submodules
                    parts = identifier.split(".")
                    identifier = next((".".join(parts[:n]) for n in range(len(parts), 1, -1) if any(".".join(parts[:n]) in m for m in MARKERS.values())), identifier)
                for generation, markers in MARKERS.items():
                    if identifier in markers and (identifier, line) not in seen:
                        seen.add((identifier, line))
                        counts[generation] += 1
                        if len(found[generation]) < samples:
                            found[generation].append({"name": identifier, "path": relative, "line": line})
        if truncated:
            break
    return {"files_importing": files[:30], "counts": counts, "samples": found, "scan_truncated": truncated,
            "heuristic": True, "verified_against": VERIFIED_AGAINST}


# ---------------------------------------------------------------- recommendation

def recommend(explicit: str, pins: list[dict], markers: dict, package: dict, pypi: dict) -> dict:
    pin_generations = {p["generation"] for p in pins if p["generation"]}
    marker_generations = {g for g, n in markers["counts"].items() if n}
    installed = package.get("generation") if package.get("importable") else None
    sources = [("explicit request", {explicit} if explicit != "auto" else set()), ("project pins", pin_generations),
               ("code markers", marker_generations), ("installed package", {installed} if installed else set())]
    generation = None
    reason = "new work: v2 is the maintained line; pin an exact version in a dedicated virtual environment"
    new_project = True
    for label, generations in sources:
        if len(generations) == 1:
            generation, reason, new_project = next(iter(generations)), f"{label} (highest-precedence evidence found)", False
            break
        if len(generations) > 1:
            reason, new_project = f"{label} disagree; inspect the file being changed and pass --generation", False
            break
    else:
        generation = "v2"
    conflicts = [f"{label}: {', '.join(sorted(gens - {generation}))}" for label, gens in sources
                 if generation and gens - {generation}]
    if markers["scan_truncated"]:
        conflicts.append("marker scan truncated at 300 files; inspect the files being changed")
    result = {"generation": generation, "version": None, "docs_ref": None, "approximate": True,
              "release_candidate": False, "new_project": new_project, "reason": reason, "conflicts": conflicts}
    if not generation:
        return result
    exact = [p for p in pins if p["exact"] and p["generation"] == generation]
    if exact:
        version, basis, guessed = exact[0]["version"], exact[0]["source"], False
    elif installed == generation:
        version, basis, guessed = package.get("version") or package.get("distribution_version"), "installed package", False
    else:
        version, basis, guessed = (pypi.get("latest_by_generation") or {}).get(generation), "latest PyPI release of that generation", True
    if version:
        ref, moving = ref_for_version(version)
        parsed = parse_version(version)
        result.update(version=version, docs_ref=ref, version_basis=basis, approximate=guessed or moving,
                      release_candidate=bool(parsed and parsed["prerelease"] and not parsed["dev"]))
    else:
        result.update(docs_ref="develop_v1" if generation == "v1" else "develop", version_basis="no version evidence; moving branch")
    return result


def cached_refs(root: Path) -> list[str]:
    refs = []
    for path in sorted((root / "refs").glob("*/manifest.json")):
        try:
            refs.append(json.loads(path.read_text())["ref"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return refs


def doctor(args: argparse.Namespace) -> dict:
    project = absolute(args.project)
    if not project.is_dir():
        raise ContextError("Project directory not found; pass --project /path/to/project.", 2)
    python = python_path(project, args.python)
    probe = probe_python(python, project)
    pins, crates, prerelease = pins_and_crates(project)
    markers = marker_scan(project)
    pypi = pypi_status(args.offline)
    root = cache_root(args.cache_dir)
    return {**probe, "project": str(project),
            "project_evidence": {"pins": pins, "uv_prerelease": prerelease, "crates": crates, "markers": markers},
            "pypi": pypi, "recommendation": recommend(args.generation, pins, markers, probe["package"], pypi),
            "cache_root": str(root), "cached_refs": cached_refs(root),
            "docs": {"hosted_latest": "https://nautilustrader.io/docs/latest/", "llms_txt": "https://nautilustrader.io/docs/llms.txt"}}


# ---------------------------------------------------------------- docs cache

def normalize_ref(value: str) -> str:
    ref = value.strip()
    if parse_version(ref):
        ref = "v" + ref
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref) or ".." in ref or ref.endswith((".lock", "/")):
        raise ContextError("Use a git tag such as v1.231.0 or v2.0.0rc5, or a branch such as develop, develop_v1 or nightly.", 2)
    return ref


def is_tag(ref: str) -> bool:
    return bool(re.fullmatch(r"v\d+\.\d+\.\d+.*", ref))


def remote_commit(url: str, ref: str) -> str | None:
    names = [f"refs/tags/{ref}", f"refs/tags/{ref}^{{}}"] if is_tag(ref) else [f"refs/heads/{ref}"]
    output = run(["git", "ls-remote", url, *names], timeout=60, label="git ls-remote").stdout.decode()
    rows = {}
    for line in output.splitlines():
        sha, _, name = line.partition("\t")
        rows[name] = sha
    # Annotated tags list the tag object first; the peeled ^{} row is the commit.
    return rows.get(f"refs/tags/{ref}^{{}}") or rows.get(names[0])


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def commit_manifest(directory: Path, manifest: dict) -> None:
    temporary = directory / f".manifest-{uuid.uuid4().hex}.tmp"
    try:
        write_json(temporary, manifest)
        os.replace(temporary, directory / "manifest.json")
    finally:
        temporary.unlink(missing_ok=True)


def current_cache(directory: Path, ref: str) -> tuple[dict, Path] | None:
    try:
        manifest = json.loads((directory / "manifest.json").read_text())
        generation = manifest["generation"]
        if manifest["schema"] != SCHEMA or manifest["ref"] != ref or not re.fullmatch(r"[a-f0-9]{32}", generation):
            return None
        base = directory / "generations" / generation
        if not base.is_dir() or not isinstance(manifest["files"], int) or manifest["files"] < 1:
            return None
        return manifest, base
    except (OSError, ValueError, KeyError, TypeError):
        return None


def cache_result(status: str, manifest: dict, base: Path, **extra) -> dict:
    return {"status": status, "ref": manifest["ref"], "kind": manifest["kind"], "commit": manifest["commit"],
            "root": str(base), "docs_dir": str(base / "docs") if (base / "docs").is_dir() else None,
            "examples_dir": str(base / "examples") if (base / "examples").is_dir() else None,
            "root_files": {name: str(base / name) if (base / name).is_file() else None for name in ROOT_FILES},
            "files": manifest["files"], "checked_at": manifest["checked_at"],
            "manifest": str(base.parent.parent / "manifest.json"), **extra}


@contextmanager
def ref_lock(directory: Path):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ContextError("Another process is updating this ref; retry after it completes.") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def sync_docs(root: Path, ref: str, *, refresh: bool = False, offline: bool = False, dry_run: bool = False) -> dict:
    ref = normalize_ref(ref)
    url = os.environ.get("NAUTILUS_AGENT_REPO_URL", REPO_URL)
    kind = "tag" if is_tag(ref) else "branch"
    directory = root / "refs" / ref.replace("/", "__")
    old = current_cache(directory, ref)
    if offline:
        if not old:
            raise ContextError(f"No valid cache for {ref}. Run docs --ref {ref} online first.", 2)
        return cache_result("offline", *old)
    if dry_run:
        try:
            commit, warning = remote_commit(url, ref), None
        except ContextError as exc:
            commit, warning = None, str(exc)
        action = "none" if old and commit == old[0]["commit"] else "clone" if commit else "unknown"
        return {"status": "dry_run", "ref": ref, "kind": kind, "directory": str(directory), "remote_commit": commit,
                "cache_available": bool(old), "cached_commit": old[0]["commit"] if old else None, "action": action,
                "sparse_patterns": list(SPARSE), **({"warning": warning} if warning else {})}
    with ref_lock(directory):
        old = current_cache(directory, ref)
        now = time.time()
        if old and not refresh and (kind == "tag" or 0 <= now - old[0]["checked_at"] < TTL):
            return cache_result("cached", *old)
        try:
            commit = remote_commit(url, ref)
        except ContextError as exc:
            if old:
                log(f"{exc} Using the previous cache; freshness is unknown.")
                return cache_result("stale", *old, warning=str(exc))
            raise
        if not commit:
            if old:
                return cache_result("stale", *old, warning=f"{ref} no longer exists upstream; cache kept.")
            raise ContextError(f"{ref} was not found upstream. Use a release tag (v1.231.0, v2.0.0rcN) or a branch (develop, develop_v1, nightly); list tags with git ls-remote --tags {REPO_URL}.", 2)
        if old and old[0]["commit"] == commit:
            manifest = {**old[0], "checked_at": now}
            commit_manifest(directory, manifest)
            return cache_result("unchanged", manifest, old[1])
        generations = directory / "generations"
        generations.mkdir(exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=generations))
        try:
            checkout = stage / "checkout"
            run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout", "--branch", ref, url, str(checkout)], timeout=300, label="git clone")
            run(["git", "-C", str(checkout), "sparse-checkout", "set", "--no-cone", *SPARSE], label="git sparse-checkout")
            run(["git", "-C", str(checkout), "checkout", "--quiet", ref], timeout=300, label="git checkout")
            cloned = run(["git", "-C", str(checkout), "rev-parse", "HEAD"], label="git rev-parse").stdout.decode().strip()
            if cloned != commit:
                raise ContextError(f"{ref} moved during sync ({commit[:12]} -> {cloned[:12]}); retry.", 4)
            shutil.rmtree(checkout / ".git")
            files = sum(1 for p in checkout.rglob("*") if p.is_file())
            if not files:
                raise ContextError(f"{ref} has no docs, examples or root guides; previous cache is preserved.", 4)
            generation = uuid.uuid4().hex
            target = generations / generation
            checkout.rename(target)
            manifest = {"schema": SCHEMA, "ref": ref, "kind": kind, "commit": commit, "repo": url,
                        "generation": generation, "checked_at": now, "files": files, "sparse": list(SPARSE)}
            commit_manifest(directory, manifest)
            keep = {generation, old[0]["generation"] if old else None}
            for item in generations.iterdir():
                # Keep the previous generation for readers that resolved it before this swap.
                if item.name not in keep and not item.name.startswith(".staging-"):
                    shutil.rmtree(item, ignore_errors=True)
            return cache_result("updated", manifest, target)
        finally:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)


# ---------------------------------------------------------------- CLI

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog="JSON stdout; diagnostics stderr. Exit codes: 0 success (including explicitly marked stale cache), "
                                       "2 input/cache missing, 3 external failure, 4 validation failure. macOS/Linux. "
                                       "NAUTILUS_AGENT_REPO_URL overrides the git remote (mirrors, tests).")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("doctor", "docs"):
        cmd = sub.add_parser(name, help="detect generation and version" if name == "doctor" else "sync version-matched docs")
        cmd.add_argument("--project", default=".", help="Project root to inspect (default: current directory)")
        cmd.add_argument("--python", help="Project Python; otherwise .venv then the helper interpreter")
        cmd.add_argument("--cache-dir", help=f"Override the XDG cache root (default ~/.cache/{CACHE_NAME})")
        cmd.add_argument("--offline", action="store_true", help="No network: skip PyPI (doctor) or use only valid cache (docs)")
        cmd.add_argument("--generation", choices=("auto", "v1", "v2"), default="auto", help="Explicit generation from the user")
        if name == "docs":
            cmd.add_argument("--ref", help="Git tag (v1.231.0, 2.0.0rc5) or branch; otherwise doctor's recommendation")
            group = cmd.add_mutually_exclusive_group()
            group.add_argument("--refresh", action="store_true", help="Check the remote commit now, even for a cached tag or within the 24-hour branch TTL")
            group.add_argument("--dry-run", action="store_true", help="Read the remote commit and report the planned action without writing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(args)
        else:
            if args.offline and (args.refresh or args.dry_run):
                raise ContextError("--offline cannot be combined with --refresh or --dry-run.", 2)
            ref = args.ref
            if not ref:
                report = doctor(args)
                ref = report["recommendation"]["docs_ref"]
                if not ref:
                    raise ContextError("No single generation was identified (" + report["recommendation"]["reason"] + "). Pass --ref or --generation.", 2)
                log(f"Using {ref}: {report['recommendation']['reason']}.")
            result = sync_docs(cache_root(args.cache_dir), ref, refresh=args.refresh, offline=args.offline, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ContextError, OSError) as exc:
        log(str(exc))
        return getattr(exc, "code", 3)


if __name__ == "__main__":
    raise SystemExit(main())
