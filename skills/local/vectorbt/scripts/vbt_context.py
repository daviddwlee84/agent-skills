#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Inspect VectorBT environments and synchronize private release documentation.

No VectorBT import is needed in this helper's own environment. Downloads use gh's
existing authentication. A manifest atomically selects an immutable generation;
readers already using an older generation remain valid during a refresh.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
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
from urllib.parse import quote, urlsplit
import uuid

REPO = "polakowo/vectorbt.pro"
ASSETS = ("pages", "examples", "messages")
TTL = 24 * 60 * 60
SCHEMA = 1


class ContextError(Exception):
    def __init__(self, message: str, code: int = 3, access: str = "unknown"):
        super().__init__(message)
        self.code = code
        self.access = access


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
        return Path(xdg) / "vectorbt-agent"
    if xdg:
        log("Ignoring relative XDG_CACHE_HOME; using ~/.cache/vectorbt-agent.")
    return Path.home() / ".cache" / "vectorbt-agent"


def release_tag(value: str) -> str:
    tag = value if value.startswith("v") else "v" + value
    if not re.fullmatch(r"v[0-9][A-Za-z0-9._+-]*", tag):
        raise ContextError("Use a concrete release, for example v2026.9.5; latest and paths are not accepted.", 2)
    return tag


def run(args: list[str], *, cwd: Path | None = None, timeout: float = 90) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContextError(f"Cannot run {Path(args[0]).name}: {type(exc).__name__}. Check the executable and connection.") from exc
    if result.returncode:
        # Never echo arbitrary gh stderr: it may contain credentials or URLs.
        stderr = result.stderr.decode(errors="replace")
        match = re.search(r"HTTP (\d{3})", stderr)
        status = match.group(1) if match else None
        denied = status in {"401", "403", "404"}
        hint = "Check gh auth status, repository invitation and account access." if Path(args[0]).name == "gh" else "Check the interpreter and its installed dependencies."
        raise ContextError(f"{Path(args[0]).name} failed" + (f" (HTTP {status})" if status else "") + f". {hint}", access="denied" if denied else "unknown")
    return result


def gh_json(endpoint: str) -> dict:
    try:
        return json.loads(run(["gh", "api", endpoint]).stdout)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ContextError("GitHub returned invalid JSON; retry the metadata request.") from exc


def pro_access(offline: bool = False) -> dict:
    if offline:
        return {"status": "unknown", "reason": "offline; access was not checked"}
    try:
        repo = gh_json(f"repos/{REPO}")
        if repo.get("full_name", "").lower() != REPO.lower():
            raise ContextError("Unexpected repository response; PRO access is not confirmed.")
        return {"status": "allowed", "reason": "private repository read succeeded"}
    except ContextError as exc:
        return {"status": exc.access, "reason": str(exc)}


def python_path(project: Path, explicit: str | None) -> Path:
    if explicit:
        found = shutil.which(explicit) if os.sep not in explicit else explicit
        if not found:
            raise ContextError("Python executable not found; pass --python /absolute/path/to/python.", 2)
        return absolute(found)
    for candidate in (project / ".venv/bin/python", project / ".venv/Scripts/python.exe"):
        if candidate.exists():
            return absolute(candidate)
    return absolute(sys.executable)


PROBE = r'''
import contextlib, importlib, importlib.metadata, importlib.util, io, json, sys
out = {"python": sys.executable, "python_version": sys.version.split()[0], "packages": {}}
for name in ("vectorbt", "vectorbtpro"):
    item = {"installed": False, "importable": False}
    try:
        item["distribution_version"] = importlib.metadata.version(name)
        item["installed"] = True
    except importlib.metadata.PackageNotFoundError:
        pass
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            spec = importlib.util.find_spec(name)
            if spec is not None:
                item["origin"] = spec.origin
                module = importlib.import_module(name)
                item["version"] = str(getattr(module, "version", None) or getattr(module, "__version__", ""))
                item["importable"] = True
    except Exception as exc:
        item["import_error"] = type(exc).__name__
    out["packages"][name] = item
print(json.dumps(out))
'''


def probe_python(python: Path, project: Path) -> dict:
    try:
        return json.loads(run([str(python), "-c", PROBE], cwd=project).stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ContextError("Interpreter probe did not return JSON; inspect the target Python environment.") from exc


def project_evidence(project: Path) -> dict:
    editions: set[str] = set()
    sources: list[str] = []
    project_file = project / "pyproject.toml"
    if project_file.exists():
        try:
            config = tomllib.loads(project_file.read_text())
            deps = config.get("project", {}).get("dependencies", [])
            for dep in deps:
                match = re.match(r"(vectorbtpro|vectorbt)(?=[\[\s<>=!~;@]|$)", dep, re.I)
                if match:
                    editions.add("pro" if match[1].lower() == "vectorbtpro" else "oss")
                    sources.append("pyproject.toml")
        except (ValueError, OSError) as exc:
            raise ContextError("Cannot read project dependencies; repair pyproject.toml or specify another --project.", 2) from exc
    skipped = {".git", ".venv", "venv", "node_modules", ".agents", ".claude", ".knowledge", "__pycache__", "site"}
    count = 0
    truncated = False
    for directory, children, files in os.walk(project):
        children[:] = sorted(x for x in children if x not in skipped and not x.startswith("."))
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            count += 1
            if count > 300:
                truncated = True
                break
            path = Path(directory) / name
            if path.stat().st_size > 1_000_000:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, SyntaxError):
                continue
            modules = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    modules.append(node.module.split(".")[0])
            for module in modules:
                if module in {"vectorbt", "vectorbtpro"}:
                    editions.add("pro" if module == "vectorbtpro" else "oss")
                    sources.append(str(path.relative_to(project)))
        if truncated:
            break
    return {"editions": sorted(editions), "sources": sorted(set(sources))[:30], "scan_truncated": truncated}


def choose_edition(explicit: str, evidence: dict, packages: dict, access: str) -> dict:
    if explicit != "auto":
        return {"edition": explicit, "reason": "explicit request"}
    editions = evidence["editions"]
    if len(editions) == 1:
        return {"edition": editions[0], "reason": "existing project; preserve its edition"}
    if len(editions) > 1 or evidence.get("scan_truncated"):
        return {"edition": None, "reason": "inspect the file being changed, then pass --edition oss or pro"}
    if access == "allowed":
        return {"edition": "pro", "reason": "no project edition was found; prefer PRO with confirmed access"}
    installed = [edition for edition, name in (("oss", "vectorbt"), ("pro", "vectorbtpro")) if packages.get(name, {}).get("importable")]
    if len(installed) == 1:
        return {"edition": installed[0], "reason": "available interpreter; no project edition was found"}
    if len(installed) > 1:
        return {"edition": None, "reason": "both editions are available; select the task's edition"}
    return {"edition": "pro" if access == "allowed" else "oss", "reason": "new environment; prefer PRO when access is confirmed, otherwise OSS is available"}


def doctor(args: argparse.Namespace) -> dict:
    project = absolute(args.project)
    python = python_path(project, args.python)
    probe = probe_python(python, project)
    evidence = project_evidence(project)
    access = pro_access(args.offline)
    root = cache_root(args.cache_dir)
    releases = sorted(p.parent.name for p in (root / "pro").glob("*/manifest.json"))
    return {**probe, "project": str(project), "project_evidence": evidence, "pro_access": access,
            "recommendation": choose_edition(args.edition, evidence, probe["packages"], access["status"]),
            "cache_root": str(root), "cached_pro_releases": releases,
            "oss_docs": "https://vectorbt.dev/", "pro_docs": "https://members.vectorbt.pro/"}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def commit_manifest(directory: Path, manifest: dict) -> None:
    temporary = directory / f".manifest-{uuid.uuid4().hex}.tmp"
    try:
        write_json(temporary, manifest)
        os.replace(temporary, directory / "manifest.json")
    finally:
        temporary.unlink(missing_ok=True)


def current_cache(directory: Path, required: set[str]) -> tuple[dict, Path] | None:
    try:
        manifest = json.loads((directory / "manifest.json").read_text())
        generation = manifest["generation"]
        if manifest["schema"] != SCHEMA or manifest["release"] != directory.name or not re.fullmatch(r"[a-f0-9]{32}", generation):
            return None
        base = directory / "generations" / generation
        if not (base / "index.jsonl").is_file() or not (base / "markdown").is_dir():
            return None
        for name in required:
            if name not in manifest["assets"] or sha256(base / "raw" / f"{name}.json.gz") != manifest["assets"][name]["sha256"]:
                return None
        return manifest, base
    except (OSError, ValueError, KeyError, TypeError):
        return None


def cache_result(status: str, manifest: dict, base: Path, **extra) -> dict:
    return {"status": status, "edition": "pro", "release": manifest["release"],
            "raw_dir": str(base / "raw"), "markdown_dir": str(base / "markdown"),
            "index": str(base / "index.jsonl"), "manifest": str(base.parent.parent / "manifest.json"),
            "assets": sorted(manifest["assets"]), "checked_at": manifest["checked_at"], **extra}


@contextmanager
def release_lock(directory: Path):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ContextError("Another process is updating this release; retry after it completes.") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def read_asset(path: Path) -> list[dict]:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            items = json.load(stream)
        if not isinstance(items, list) or not items or not all(isinstance(x, dict) and isinstance(x.get("link"), str) and (x.get("content") is None or isinstance(x["content"], str)) for x in items):
            raise ValueError("expected nonempty list of linked content records")
        return items
    except (OSError, EOFError, ValueError, TypeError) as exc:
        raise ContextError(f"Invalid {path.name}: expected a GZIP JSON list of linked content records. Previous cache is preserved.", 4) from exc


def document_name(link: str) -> str:
    url = urlsplit(link)
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", url.netloc + url.path).strip("-")[:100] or "document"
    return slug + "-" + hashlib.sha256(link.encode()).hexdigest()[:16] + ".md"


def render_assets(data: dict[str, list[dict]], base: Path, release: str) -> None:
    markdown = base / "markdown"
    markdown.mkdir()
    with (base / "index.jsonl").open("w", encoding="utf-8") as index:
        def record(item: dict, path: Path, line: int, asset: str) -> None:
            row = {"edition": "pro", "release": release, "asset": asset, "url": item["link"],
                   "title": item.get("name") or item.get("title") or "", "path": str(path.relative_to(base)), "line": line}
            for key in ("obj_type", "github_link", "verified", "parent", "reference", "channel"):
                if key in item:
                    row[key] = item[key]
            index.write(json.dumps(row, ensure_ascii=False) + "\n")

        pages = data.get("pages", [])
        by_link = {x["link"]: x for x in pages}
        if len(by_link) != len(pages):
            raise ContextError("Duplicate page/heading URLs in asset; cannot build an unambiguous index.", 4)
        groups: dict[str, list[dict]] = {}
        for item in pages:
            cursor = item
            visited = set()
            while cursor.get("type") != "page" and cursor.get("parent") in by_link:
                if cursor["link"] in visited:
                    raise ContextError("Cycle in page parents; previous cache is preserved.", 4)
                visited.add(cursor["link"])
                cursor = by_link[cursor["parent"]]
            groups.setdefault(cursor["link"], []).append(item)
        page_dir = markdown / "pages"
        page_dir.mkdir()
        for root, items in groups.items():
            # Walk child order, but never fold a child page into its parent page.
            members = {x["link"]: x for x in items}
            ordered, seen = [], set()
            def visit(link: str) -> None:
                if link in seen or link not in members:
                    return
                seen.add(link)
                node = members[link]
                ordered.append(node)
                for child in node.get("children") or []:
                    visit(child)
            visit(root)
            for item in items:
                visit(item["link"])
            path = page_dir / document_name(root)
            chunks = [f"<!-- VectorBT PRO {release}; source: {root} -->\n\n"]
            line = 3
            for item in ordered:
                record(item, path, line, "pages")
                heading = item.get("name") or "Section"
                match = re.fullmatch(r"heading (\d+)", item.get("type", ""))
                level = min(6, max(1, int(match[1]))) if match else 1
                chunk = f"{'#' * level} {heading}\n\nSource: {item['link']}\n\n{item.get('content') or ''}\n\n"
                chunks.append(chunk)
                line += chunk.count("\n")
            path.write_text("".join(chunks), encoding="utf-8")

        grouped_examples: dict[str, list[dict]] = {}
        for item in data.get("examples", []):
            grouped_examples.setdefault(item["link"], []).append(item)
        example_dir = markdown / "examples"
        example_dir.mkdir()
        for link, items in grouped_examples.items():
            path = example_dir / document_name(link)
            line = 1
            with path.open("w", encoding="utf-8") as stream:
                for item in items:
                    record(item, path, line, "examples")
                    chunk = f"## {item.get('title') or 'Example'}\n\nEdition: PRO; release: {release}; source: {link}\n\nUpstream verified: {json.dumps(item.get('verified'))} (not a local test result).\n\n{item.get('description') or ''}\n\n{item.get('content') or ''}\n\n"
                    stream.write(chunk)
                    line += chunk.count("\n")
        if "messages" in data:
            # Avoid tens of thousands of tiny files; preserve reply metadata intact.
            path = markdown / "messages.jsonl"
            with path.open("w", encoding="utf-8") as stream:
                for line, item in enumerate(data["messages"], 1):
                    record(item, path, line, "messages")
                    stream.write(json.dumps({**item, "edition": "pro", "release": release}, ensure_ascii=False) + "\n")


def sync_pro(root: Path, release: str, requested: set[str], *, refresh: bool = False, offline: bool = False, dry_run: bool = False) -> dict:
    release = release_tag(release)
    if not requested or not requested <= set(ASSETS):
        raise ContextError("Choose assets from pages, examples, messages.", 2)
    directory = root / "pro" / release
    old = current_cache(directory, requested)
    if offline:
        if not old:
            raise ContextError("No complete valid cache for this release. Run sync-pro online with the same assets first.", 2)
        return cache_result("offline", *old)
    if dry_run:
        metadata = gh_json(f"repos/{REPO}/releases/tags/{quote(release, safe='')}")
        return {"status": "dry_run", "release": release, "directory": str(directory), "requested_assets": sorted(requested), "remote_assets": [x["name"] for x in metadata.get("assets", []) if x.get("name") in {f"{n}.json.gz" for n in ASSETS}], "cache_available": bool(old)}
    with release_lock(directory):
        old = current_cache(directory, requested)
        if old and not refresh and 0 <= time.time() - old[0]["checked_at"] < TTL:
            return cache_result("cached", *old)
        try:
            metadata = gh_json(f"repos/{REPO}/releases/tags/{quote(release, safe='')}")
        except ContextError as exc:
            if old:
                log(str(exc) + " Using the previous cache; freshness is unknown.")
                return cache_result("stale", *old, warning=str(exc))
            raise
        if metadata.get("tag_name") != release:
            raise ContextError("GitHub returned a different release; refusing to mix versions.", 4)
        remote = {x["name"]: x for x in metadata.get("assets", [])}
        wanted = requested | (set(old[0]["assets"]) if old else set())
        fingerprints = {}
        for name in sorted(wanted):
            item = remote.get(f"{name}.json.gz")
            if not item:
                raise ContextError(f"Release {release} has no {name}.json.gz. Select available files with --assets (for example --assets pages); do not substitute another release.", 2)
            fingerprints[name] = {k: item.get(k) for k in ("id", "name", "updated_at", "size", "digest")}
        now = time.time()
        if old and all(all(old[0]["assets"][name].get(k) == v for k, v in fp.items()) for name, fp in fingerprints.items()):
            manifest = {**old[0], "checked_at": now}
            commit_manifest(directory, manifest)
            return cache_result("unchanged", manifest, old[1])
        generations = directory / "generations"
        generations.mkdir(exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=generations))
        try:
            (stage / "raw").mkdir()
            data = {}
            for name, fp in fingerprints.items():
                path = stage / "raw" / f"{name}.json.gz"
                previous = old[0]["assets"].get(name) if old else None
                if previous and all(previous.get(k) == v for k, v in fp.items()):
                    shutil.copyfile(old[1] / "raw" / path.name, path)
                else:
                    run(["gh", "release", "download", release, "--repo", REPO, "--pattern", path.name, "--output", str(path)], timeout=180)
                digest = sha256(path)
                if fp["size"] is not None and path.stat().st_size != fp["size"]:
                    raise ContextError(f"Size mismatch for {path.name}; previous cache is preserved.", 4)
                if fp["digest"] and fp["digest"] != "sha256:" + digest:
                    raise ContextError(f"Checksum mismatch for {path.name}; previous cache is preserved.", 4)
                fp["sha256"] = digest
                fp["remote_checksum_verified"] = bool(fp["digest"])
                data[name] = read_asset(path)
            render_assets(data, stage, release)
            generation = uuid.uuid4().hex
            target = generations / generation
            stage.rename(target)
            manifest = {"schema": SCHEMA, "edition": "pro", "release": release, "repo": REPO,
                        "generation": generation, "checked_at": now, "assets": fingerprints}
            commit_manifest(directory, manifest)
            return cache_result("updated", manifest, target)
        finally:
            if stage.exists():
                shutil.rmtree(stage)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, epilog="JSON stdout; diagnostics stderr. Exit codes: 0 success (including explicitly marked stale cache), 2 input/cache missing, 3 external failure, 4 validation failure. macOS/Linux; no background scheduler.")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("doctor", "sync-pro"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--project", default=".")
        cmd.add_argument("--python", help="Project Python; otherwise .venv then the helper interpreter")
        cmd.add_argument("--cache-dir", help="Override XDG cache root")
        cmd.add_argument("--offline", action="store_true")
        if name == "doctor":
            cmd.add_argument("--edition", choices=("auto", "oss", "pro"), default="auto")
        else:
            cmd.add_argument("--release", help="Concrete release; otherwise use importable vectorbtpro")
            cmd.add_argument("--assets", default="pages,examples", help="Comma-separated asset names; use pages for older releases without examples")
            cmd.add_argument("--messages", action="store_true")
            group = cmd.add_mutually_exclusive_group()
            group.add_argument("--refresh", action="store_true", help="Check metadata now, even within the 24-hour TTL")
            group.add_argument("--dry-run", action="store_true", help="Read metadata and report paths without writing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(args)
        else:
            if args.offline and (args.refresh or args.dry_run):
                raise ContextError("--offline cannot be combined with --refresh or --dry-run.", 2)
            release = args.release
            if not release:
                project = absolute(args.project)
                probe = probe_python(python_path(project, args.python), project)
                package = probe["packages"]["vectorbtpro"]
                if not package.get("importable") or not package.get("version"):
                    raise ContextError("No importable PRO version. Pass --python for the project environment, or --release for documentation-only use.", 2)
                release = package["version"]
            assets = set(args.assets.split(","))
            if args.messages:
                assets.add("messages")
            result = sync_pro(cache_root(args.cache_dir), release, assets, refresh=args.refresh, offline=args.offline, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ContextError, OSError) as exc:
        log(str(exc))
        return getattr(exc, "code", 3)


if __name__ == "__main__":
    raise SystemExit(main())
