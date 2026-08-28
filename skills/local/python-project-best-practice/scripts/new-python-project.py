#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["tyro>=0.9.5"]
# ///
"""Scaffold a modern Python project from the bundled template tree.

Copies ``assets/project/`` into a target directory, stripping the ``.tmpl``
suffix, substituting placeholders, and keeping only the files and marker
blocks that belong to the chosen ``--profile``. Writes nothing outside the
target directory and makes no network calls.

Profiles are a ladder; each adds to the one before it:

    minimal  package + tests + Justfile + CI + agent docs. No CLI.
    cli      + tyro CLI, loguru, pydantic-settings, [project.scripts]  (default)
    lib      cli, plus publishing metadata for a library others import
    api      cli, plus a FastAPI app with /docs and /openapi.json
    ml       cli, plus a marimo notebook that doubles as a batch CLI
    rust     cli, plus a PyO3 crate built by maturin

Examples:
    new-python-project.py --help             # every flag, with defaults

    # preview, write nothing
    new-python-project.py --dry-run ./my-tool

    # a CLI tool, package name derived from the directory
    new-python-project.py ./my-tool

    # a library with an explicit slug and owner
    new-python-project.py --profile lib --name churn-scorer --owner acme ./services/churn

Output:
    JSON summary on stdout; human-readable progress on stderr.

Exit codes:
    0  success
    1  unexpected runtime error
    2  usage error (bad flag, unknown profile)
    3  target exists and --force was not given
    4  the template tree and assets/manifest.toml disagree
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Literal

import tyro

PROFILES = ("minimal", "cli", "lib", "api", "ml", "rust")
Profile = Literal["minimal", "cli", "lib", "api", "ml", "rust"]

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "project"
MANIFEST = SKILL_DIR / "assets" / "manifest.toml"

_IF = re.compile(r"^\s*#\s*__IF:([a-z, ]+)__\s*$")
_END = re.compile(r"^\s*#\s*__END__\s*$")
_SLUG_OK = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def log(message: str) -> None:
    print(message, file=sys.stderr)


def die(message: str, code: int) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


@dataclasses.dataclass(frozen=True)
class Args:
    """Scaffold a modern Python project. See the module docstring for profiles."""

    target: tyro.conf.Positional[str]
    """Directory to create. Its basename becomes the default project name."""

    profile: Profile = "cli"
    """How much to generate. Each profile is a superset of `cli` except `minimal`."""

    name: str | None = None
    """Project slug (hyphen-case). Defaults to the target directory's basename."""

    description: str = "A Python project."
    """One-line description used in pyproject.toml, README, and the agent skill."""

    author: str = "Your Name"
    """Author name written into pyproject.toml."""

    owner: str = "OWNER"
    """GitHub owner used to build repository URLs."""

    python_floor: str = "3.11"
    """Minimum supported Python (requires-python, CI matrix floor)."""

    python_pin: str = "3.13"
    """Python written to .python-version and used for local development."""

    dry_run: bool = False
    """List what would be written; create nothing."""

    force: bool = False
    """Overwrite an existing non-empty target directory."""

    no_git: bool = False
    """Skip `git init` in the new project."""


def load_manifest() -> dict[str, str]:
    with MANIFEST.open("rb") as handle:
        return tomllib.load(handle)["files"]


def check_manifest(files: dict[str, str]) -> None:
    """Fail loudly when the manifest and the template tree disagree."""
    on_disk = {
        str(path.relative_to(TEMPLATE_DIR))[: -len(".tmpl")]
        for path in TEMPLATE_DIR.rglob("*.tmpl")
    }
    listed = set(files)
    if missing := sorted(listed - on_disk):
        die(
            "assets/manifest.toml lists files that do not exist: "
            + ", ".join(missing)
            + " (expected each as assets/project/<path>.tmpl)",
            4,
        )
    if unlisted := sorted(on_disk - listed):
        die(
            "template files are not listed in assets/manifest.toml: "
            + ", ".join(unlisted)
            + " (an unlisted file is never copied - add it to [files])",
            4,
        )


def wanted(spec: str, profile: str) -> bool:
    return spec.strip() == "*" or profile in spec.split()


def apply_markers(text: str, profile: str) -> str:
    """Drop `# __IF:a,b__ ... # __END__` blocks that this profile does not want.

    Marker lines are always removed; only the body between them is conditional.
    """
    out: list[str] = []
    keep_stack: list[bool] = []
    # After a block is dropped, its surrounding blank lines would double up.
    # Squeeze only those. Never touch blank lines elsewhere: two blank lines
    # between top-level defs is required formatting, not slack.
    squeeze = False
    for line in text.splitlines(keepends=True):
        if match := _IF.match(line):
            names = [name.strip() for name in match.group(1).split(",") if name.strip()]
            keep_stack.append(profile in names)
            continue
        if _END.match(line):
            if not keep_stack:
                die("unbalanced __END__ marker in template", 4)
            squeeze = not keep_stack.pop()
            continue
        if not all(keep_stack):
            continue
        if squeeze and not line.strip():
            if out and not out[-1].strip():
                continue
        squeeze = False
        out.append(line)
    if keep_stack:
        die("unclosed __IF__ marker in template", 4)
    return "".join(out)


def substitutions(args: Args, slug: str, package: str) -> dict[str, str]:
    description = args.description.strip()
    if description and not description.endswith((".", "!", "?")):
        description += "."
    return {
        "PROJECT_SLUG_PLACEHOLDER": slug,
        "PACKAGE_NAME_PLACEHOLDER": package,
        "PROJECT_DESCRIPTION_PLACEHOLDER": description,
        "AUTHOR_PLACEHOLDER": args.author,
        "OWNER_PLACEHOLDER": args.owner,
        "PYTHON_FLOOR_PLACEHOLDER": args.python_floor,
        "PYTHON_PIN_PLACEHOLDER": args.python_pin,
        "RUFF_TARGET_PLACEHOLDER": "py" + args.python_floor.replace(".", ""),
        "ABI3_PLACEHOLDER": args.python_floor.replace(".", ""),
        "ENV_PREFIX_PLACEHOLDER": package.upper() + "_",
    }


def render(text: str, subs: dict[str, str], *, yaml_safe: bool) -> str:
    for token, value in subs.items():
        if yaml_safe and token == "PROJECT_DESCRIPTION_PLACEHOLDER":
            # The self-skill embeds this inside a single-quoted YAML scalar.
            value = value.replace("'", "''")
        text = text.replace(token, value)
    return text


def destination(rel: str, slug: str, package: str) -> Path:
    parts = [package if part == "PACKAGE" else slug if part == "SLUG" else part
             for part in Path(rel).parts]
    return Path(*parts)


def main(args: Args) -> None:
    if args.profile not in PROFILES:
        die(f"unknown profile {args.profile!r}; choose one of {', '.join(PROFILES)}", 2)

    target = Path(args.target).expanduser().resolve()
    slug = (args.name or target.name).strip().lower()
    if not _SLUG_OK.match(slug):
        die(
            f"invalid project name {slug!r}: use lower-case hyphen-separated words "
            "(e.g. churn-scorer). Pass --name to override the directory basename.",
            2,
        )
    package = slug.replace("-", "_")

    if target.exists() and any(target.iterdir()) and not args.force and not args.dry_run:
        die(f"{target} exists and is not empty; pass --force to overwrite", 3)

    files = load_manifest()
    check_manifest(files)
    subs = substitutions(args, slug, package)

    written: list[str] = []
    for rel, spec in sorted(files.items()):
        if not wanted(spec, args.profile):
            continue
        source = TEMPLATE_DIR / (rel + ".tmpl")
        rel_out = destination(rel, slug, package)
        body = apply_markers(source.read_text(encoding="utf-8"), args.profile)
        body = render(body, subs, yaml_safe=rel.startswith(".agents/skills/"))
        written.append(str(rel_out))
        if args.dry_run:
            continue
        out = target / rel_out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        if rel.startswith("scripts/") and rel.endswith(".py"):
            out.chmod(0o755)

    # CLAUDE.md is a symlink so both agent conventions read one file.
    symlink = "CLAUDE.md -> AGENTS.md"
    if not args.dry_run:
        link = target / "CLAUDE.md"
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to("AGENTS.md")
    written.append("CLAUDE.md")

    git_initialised = False
    if not args.dry_run and not args.no_git and not (target / ".git").exists():
        result = subprocess.run(
            ["git", "init", "--quiet", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        git_initialised = result.returncode == 0
        if not git_initialised:
            log(f"warning: git init failed: {result.stderr.strip()}")

    extras = {
        "minimal": [],
        "cli": ["verifiable-surfaces"],
        "lib": ["verifiable-surfaces", "cli-release-distribution"],
        "api": ["verifiable-surfaces", "fastapi-ai-patterns"],
        "ml": ["mlflow-tracking", "dvc-ml-workflow", "experiment-knowledge-harness",
               "marimo-batch-mlflow"],
        "rust": ["verifiable-surfaces"],
    }[args.profile]

    next_steps = [
        f"cd {target}",
        "uv sync",
        "just check",
    ]
    if args.profile != "minimal":
        next_steps.append("just docs-sync   # populate the CLI block in AGENTS.md")
    next_steps.append("npx skills@latest add daviddwlee84/agent-skills/skills")

    summary = {
        "project": slug,
        "package": package,
        "profile": args.profile,
        "path": str(target),
        "dry_run": args.dry_run,
        "git_initialised": git_initialised,
        "symlink": symlink,
        "files": sorted(written),
        "recommended_skills": [
            "project-knowledge-harness",
            "agent-history-hygiene",
            "mkdocs-site-bootstrap",
            *extras,
        ],
        "next_steps": next_steps,
    }
    log(
        f"{'would write' if args.dry_run else 'wrote'} {len(written)} files "
        f"to {target} (profile: {args.profile})"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    os.environ.setdefault("COLUMNS", "100")
    try:
        main(tyro.cli(Args, prog="new-python-project.py", description=__doc__))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - top-level guard, message is the contract
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
