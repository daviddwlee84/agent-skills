#!/usr/bin/env python3
# mkdocs-site-bootstrap-managed: two-pass-build-v1
"""Build a strict MkDocs site without mixing static-i18n and llmstxt passes."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse


ENV_DOCS_DIR = "MKDOCS_SITE_BOOTSTRAP_DOCS_DIR"
ENV_I18N = "MKDOCS_SITE_BOOTSTRAP_I18N_ENABLED"
ENV_LLMSTXT = "MKDOCS_SITE_BOOTSTRAP_LLMSTXT_ENABLED"
ENV_COPY_TO_LLM = "MKDOCS_SITE_BOOTSTRAP_COPY_TO_LLM_ENABLED"
ENV_SOCIAL = "MKDOCS_SITE_BOOTSTRAP_SOCIAL_ENABLED"


class BuildFailure(RuntimeError):
    """A user-actionable build failure with a stable exit code."""

    def __init__(self, message: str, exit_code: int = 4) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Strictly build MkDocs, using separate default-language llmstxt and "
            "multilingual HTML passes when mkdocs-static-i18n is configured."
        ),
        epilog=(
            "Normal output is one JSON object on stdout; build logs go to stderr. "
            "Exit codes: 0 success, 2 invalid/missing input, 3 MkDocs failed, "
            "4 generated output failed validation."
        ),
    )
    parser.add_argument(
        "--target-dir",
        default=".",
        metavar="DIR",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--config-file",
        default="mkdocs.yml",
        metavar="FILE",
        help="MkDocs config, relative to --target-dir (default: mkdocs.yml).",
    )
    parser.add_argument(
        "--site-dir",
        metavar="DIR",
        help="Final output directory, relative to --target-dir; overrides mkdocs.yml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect configuration and print the planned passes without building.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary docs/build trees and report their path in JSON.",
    )
    return parser.parse_args(argv)


def unresolved_under(base: Path, value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return Path(os.path.abspath(path))


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def load_raw_config(config_file: Path) -> dict[str, Any]:
    try:
        import yaml
        from mkdocs.utils.yaml import get_yaml_loader, yaml_load
    except ImportError as error:
        raise BuildFailure(
            "MkDocs is not installed. Run `uv sync --extra docs`, then invoke this "
            "helper with `uv run python scripts/build-docs-site.py`.",
            2,
        ) from error

    try:
        with config_file.open("rb") as stream:
            direct_config = yaml.load(stream, Loader=get_yaml_loader())
        if isinstance(direct_config, dict) and "INHERIT" in direct_config:
            raise BuildFailure(
                "mkdocs.yml uses INHERIT, which the managed helper cannot safely "
                "audit. Flatten the effective config first, then run: bash "
                ".agents/skills/mkdocs-site-bootstrap/scripts/"
                "migrate-i18n-llmstxt.sh --target-dir . --apply --verify --json",
                2,
            )
        with config_file.open("rb") as stream:
            config = yaml_load(stream)
    except BuildFailure:
        raise
    except Exception as error:
        raise BuildFailure(f"Could not parse {config_file}: {error}", 2) from error
    if not isinstance(config, dict):
        raise BuildFailure(f"Expected a YAML mapping in {config_file}.", 2)
    return config


def load_config_with_env(config_file: Path, values: dict[str, str]) -> dict[str, Any]:
    previous = {name: os.environ.get(name) for name in values}
    try:
        os.environ.update(values)
        return load_raw_config(config_file)
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def plugin_definition(config: dict[str, Any], wanted: str) -> tuple[bool, dict[str, Any]]:
    plugins = config.get("plugins", [])
    if isinstance(plugins, dict):
        plugins = [{name: value} for name, value in plugins.items()]
    if not isinstance(plugins, list):
        raise BuildFailure("mkdocs.yml `plugins` must be a list or mapping.", 2)

    found: list[dict[str, Any]] = []
    for item in plugins:
        if isinstance(item, str):
            name, value = item, {}
        elif isinstance(item, dict) and len(item) == 1:
            name, value = next(iter(item.items()))
        else:
            continue
        if str(name).split("/")[-1] != wanted:
            continue
        if value is None:
            value = {}
        if not isinstance(value, dict):
            raise BuildFailure(f"Plugin `{wanted}` configuration must be a mapping.", 2)
        found.append(value)
    if len(found) > 1:
        raise BuildFailure(f"Plugin `{wanted}` is configured more than once.", 2)
    return (bool(found), found[0] if found else {})


def extension_definition(config: dict[str, Any], wanted: str) -> tuple[bool, dict[str, Any]]:
    extensions = config.get("markdown_extensions", [])
    if not isinstance(extensions, list):
        raise BuildFailure("mkdocs.yml `markdown_extensions` must be a list.", 2)
    found: list[dict[str, Any]] = []
    for item in extensions:
        if item == wanted:
            found.append({})
        elif isinstance(item, dict) and wanted in item:
            value = item[wanted]
            if value is None:
                value = {}
            elif not isinstance(value, dict):
                raise BuildFailure(f"Extension `{wanted}` configuration must be a mapping.", 2)
            found.append(value)
    if len(found) > 1:
        raise BuildFailure(f"Extension `{wanted}` is configured more than once.", 2)
    return (bool(found), found[0] if found else {})


def validate_env_contract(config_file: Path, config: dict[str, Any]) -> None:
    probe_docs = str(config_file.parent / ".mkdocs-site-bootstrap-env-probe")
    plugin_names = ("i18n", "llmstxt", "copy-to-llm", "social")
    plugin_env = {
        "i18n": ENV_I18N,
        "llmstxt": ENV_LLMSTXT,
        "copy-to-llm": ENV_COPY_TO_LLM,
        "social": ENV_SOCIAL,
    }
    present = [name for name in plugin_names if plugin_definition(config, name)[0]]
    common = {ENV_DOCS_DIR: probe_docs}
    disabled = load_config_with_env(
        config_file,
        {**common, **{variable: "false" for variable in plugin_env.values()}},
    )
    enabled = load_config_with_env(
        config_file,
        {**common, **{variable: "true" for variable in plugin_env.values()}},
    )

    missing: list[str] = []
    if disabled.get("docs_dir") != probe_docs or enabled.get("docs_dir") != probe_docs:
        missing.append("docs_dir")
    for name in present:
        _, disabled_config = plugin_definition(disabled, name)
        _, enabled_config = plugin_definition(enabled, name)
        if disabled_config.get("enabled") is not False or enabled_config.get("enabled") is not True:
            missing.append(f"plugins.{name}.enabled")
    has_snippets, snippets = extension_definition(disabled, "pymdownx.snippets")
    if has_snippets:
        base_path = snippets.get("base_path")
        values = base_path if isinstance(base_path, list) else []
        normalized: set[str] = set()
        for value in values:
            if not isinstance(value, (str, os.PathLike)):
                continue
            item = os.fspath(value).replace("\\", "/").rstrip("/")
            if item.startswith("./"):
                item = item[2:]
            normalized.add(item)
        if probe_docs not in normalized or normalized.intersection({"docs", "docs/_snippets"}):
            missing.append("markdown_extensions.pymdownx.snippets.base_path")
    if missing:
        details = ", ".join(missing)
        raise BuildFailure(
            "mkdocs.yml is missing the managed two-pass environment contract "
            f"({details}). Run: bash .agents/skills/mkdocs-site-bootstrap/scripts/"
            "migrate-i18n-llmstxt.sh --target-dir . --apply --verify --json",
            2,
        )


def configured_locales(i18n: dict[str, Any]) -> tuple[str | None, list[str]]:
    languages = i18n.get("languages", [])
    if not isinstance(languages, list):
        raise BuildFailure("Plugin `i18n.languages` must be a list.", 2)

    locales: list[str] = []
    defaults: list[str] = []
    for language in languages:
        if not isinstance(language, dict) or not isinstance(language.get("locale"), str):
            raise BuildFailure("Every `i18n.languages` entry needs a string `locale`.", 2)
        locale = language["locale"]
        locales.append(locale)
        if language.get("default") is True:
            defaults.append(locale)
    if len(set(locales)) != len(locales):
        raise BuildFailure("Plugin `i18n.languages` contains duplicate locales.", 2)
    if len(locales) > 1 and len(defaults) != 1:
        raise BuildFailure(
            "A multilingual build needs exactly one `i18n.languages` entry with "
            "`default: true`.",
            2,
        )
    if len(locales) > 1 and i18n.get("docs_structure", "suffix") != "suffix":
        raise BuildFailure(
            "This managed helper supports only `i18n.docs_structure: suffix`.", 2
        )
    default = defaults[0] if defaults else (locales[0] if locales else None)
    return default, locales


def assert_safe_tree(source: Path, target: Path, site_dir: Path) -> None:
    if not source.exists() or not source.is_dir():
        raise BuildFailure(f"Docs directory not found: {source}", 2)
    if source.is_symlink():
        raise BuildFailure(f"Refusing symlinked docs directory: {source}", 2)
    for root, dirs, files in os.walk(source, followlinks=False):
        root_path = Path(root)
        for name in [*dirs, *files]:
            candidate = root_path / name
            if candidate.is_symlink():
                raise BuildFailure(
                    f"Refusing symlink inside docs tree: {candidate.relative_to(source)}", 2
                )

    if not is_relative_to(source, target):
        raise BuildFailure(
            f"Docs directory must stay inside --target-dir: {source} (target: {target}).",
            2,
        )
    if not is_relative_to(site_dir, target) or site_dir == target:
        raise BuildFailure(
            f"Site directory must be a child of --target-dir, not {site_dir}.", 2
        )
    if (
        site_dir == source
        or is_relative_to(source, site_dir)
        or is_relative_to(site_dir, source)
    ):
        raise BuildFailure("site_dir and docs_dir may not contain one another.", 2)
    if site_dir.is_symlink():
        raise BuildFailure(f"Refusing symlinked site directory: {site_dir}", 2)
    if site_dir.exists() and not site_dir.is_dir():
        raise BuildFailure(f"site_dir exists but is not a directory: {site_dir}", 2)


def is_translated_source(path: Path, nondefault_locales: Iterable[str]) -> bool:
    name = path.name.casefold()
    return any(
        name.endswith(f".{locale.casefold()}{extension}")
        for locale in nondefault_locales
        for extension in (".md", ".markdown")
    )


def copy_docs_tree(
    source: Path,
    destination: Path,
    *,
    nondefault_locales: Iterable[str] = (),
) -> None:
    blocked = tuple(nondefault_locales)

    def ignore(directory: str, names: list[str]) -> list[str]:
        base = Path(directory)
        return [name for name in names if is_translated_source(base / name, blocked)]

    shutil.copytree(source, destination, ignore=ignore if blocked else None)


def run_mkdocs(
    *,
    target: Path,
    config_file: Path,
    docs_dir: Path,
    site_dir: Path,
    i18n: bool,
    llmstxt: bool,
    copy_to_llm: bool,
    social: bool,
    label: str,
) -> None:
    env = os.environ.copy()
    env.update(
        {
            ENV_DOCS_DIR: str(docs_dir),
            ENV_I18N: str(i18n).lower(),
            ENV_LLMSTXT: str(llmstxt).lower(),
            ENV_COPY_TO_LLM: str(copy_to_llm).lower(),
            ENV_SOCIAL: str(social).lower(),
        }
    )
    command = [
        sys.executable,
        "-m",
        "mkdocs",
        "build",
        "--clean",
        "--strict",
        "--config-file",
        str(config_file),
        "--site-dir",
        str(site_dir),
    ]
    log(f"[{label}] {' '.join(shlex.quote(part) for part in command)}")
    completed = subprocess.run(
        command,
        cwd=target,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=sys.stderr,
        stderr=sys.stderr,
        check=False,
    )
    if completed.returncode != 0:
        raise BuildFailure(
            f"MkDocs {label} failed with exit code {completed.returncode}. "
            "Fix the strict-build diagnostics above and retry.",
            3,
        )


def llmstxt_expected_pages(config: dict[str, Any], docs_dir: Path) -> set[str]:
    present, llms = plugin_definition(config, "llmstxt")
    if not present:
        return set()
    sections = llms.get("sections", {})
    if not isinstance(sections, dict):
        raise BuildFailure("Plugin `llmstxt.sections` must be a mapping.", 2)
    source_uris = [
        path.relative_to(docs_dir).as_posix()
        for path in docs_dir.rglob("*")
        if path.is_file()
    ]
    expected: set[str] = set()
    for inputs in sections.values():
        if not isinstance(inputs, list):
            raise BuildFailure("Every `llmstxt.sections` value must be a list.", 2)
        for item in inputs:
            value = next(iter(item)) if isinstance(item, dict) and item else item
            if not isinstance(value, str):
                raise BuildFailure("llmstxt section entries must be paths or path mappings.", 2)
            if "*" in value:
                expected.update(fnmatch.filter(source_uris, value))
            else:
                expected.add(value)
    return expected


def safe_output_path(value: Any, label: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise BuildFailure(f"Plugin `llmstxt.{label}` must be a non-empty path.", 2)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise BuildFailure(f"Plugin `llmstxt.{label}` must stay inside site_dir: {value}", 2)
    return path


def generated_sidecars(site_dir: Path) -> list[Path]:
    return sorted(path for path in site_dir.rglob("*.md") if path.is_file())


def local_markdown_links(llms_file: Path, site_url: str) -> list[Path]:
    parsed_site = urlparse(site_url)
    base_path = parsed_site.path.rstrip("/") + "/"
    links: list[Path] = []
    destinations: list[str] = []
    for line in llms_file.read_text("utf-8").splitlines():
        match = re.match(r"^\s*-\s+\[[^]]*\]\((.+?)\)(?::.*)?\s*$", line)
        if match:
            destinations.append(match.group(1))
    for destination in destinations:
        parsed = urlparse(destination.strip("<>"))
        if parsed.scheme or parsed.netloc:
            if (parsed.scheme, parsed.netloc) != (parsed_site.scheme, parsed_site.netloc):
                continue
            path = parsed.path
        elif parsed.path.startswith("/"):
            path = parsed.path
        else:
            path = base_path + parsed.path
        if not path.startswith(base_path):
            raise BuildFailure(
                f"Generated llms.txt contains a local URL outside site_url: {destination}"
            )
        relative = unquote(path[len(base_path) :]).lstrip("/")
        candidate = Path(relative)
        if candidate.suffix == ".md":
            if candidate.is_absolute() or ".." in candidate.parts:
                raise BuildFailure(f"Unsafe generated Markdown URL: {destination}")
            links.append(candidate)
    return links


def has_locale_path(path: Path, nondefault_locales: Iterable[str]) -> bool:
    folded_parts = {part.casefold() for part in path.parts}
    name = path.name.casefold()
    return any(
        locale.casefold() in folded_parts
        or name.endswith(f".{locale.casefold()}.md")
        for locale in nondefault_locales
    )


def verify_llms_output(
    *,
    site_dir: Path,
    config: dict[str, Any],
    docs_dir: Path,
    site_url: str,
    full_output: Path | None,
    nondefault_locales: list[str],
) -> tuple[list[Path], list[Path]]:
    llms_file = site_dir / "llms.txt"
    if not llms_file.is_file() or not llms_file.read_text("utf-8").strip():
        raise BuildFailure("llmstxt pass did not produce a non-empty llms.txt.")
    if full_output is not None:
        full_file = site_dir / full_output
        if not full_file.is_file() or not full_file.read_text("utf-8").strip():
            raise BuildFailure(f"llmstxt pass did not produce a non-empty {full_output}.")

    sidecars = generated_sidecars(site_dir)
    expected = llmstxt_expected_pages(config, docs_dir)
    if len(sidecars) < len(expected):
        raise BuildFailure(
            f"llmstxt generated {len(sidecars)} Markdown sidecars for "
            f"{len(expected)} configured pages."
        )
    links = local_markdown_links(llms_file, site_url)
    if len(set(links)) < len(expected):
        raise BuildFailure(
            f"llms.txt links to {len(set(links))} Markdown pages but "
            f"{len(expected)} are configured."
        )
    for relative in [*sidecars, *(site_dir / link for link in links)]:
        checked = relative.relative_to(site_dir)
        if has_locale_path(checked, nondefault_locales):
            raise BuildFailure(
                f"Default-language LLM output unexpectedly contains locale path: {checked}"
            )
        if not relative.is_file():
            raise BuildFailure(f"Generated llms.txt points to missing local file: {checked}")
    return sidecars, links


def copy_artifacts(
    source_site: Path,
    destination: Path,
    *,
    full_output: Path | None,
    include_sidecars: bool,
) -> int:
    artifacts = [Path("llms.txt")]
    if full_output is not None:
        artifacts.append(full_output)
    if include_sidecars:
        artifacts.extend(path.relative_to(source_site) for path in generated_sidecars(source_site))
    copied = 0
    for relative in artifacts:
        source = source_site / relative
        if not source.is_file():
            raise BuildFailure(f"Required generated artifact is missing: {source}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += int(relative.suffix == ".md")
    return copied


def verify_multilingual_html(site_dir: Path, nondefault_locales: list[str]) -> None:
    if not any(site_dir.rglob("*.html")):
        raise BuildFailure("Multilingual pass produced no HTML files.")
    for locale in nondefault_locales:
        locale_root = site_dir / locale
        if not locale_root.is_dir() or not any(locale_root.rglob("*.html")):
            raise BuildFailure(f"Multilingual pass produced no HTML for locale {locale!r}.")


def atomic_replace_tree(staged: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = destination.parent / f".{destination.name}.backup-{uuid.uuid4().hex}"
    had_destination = destination.exists()
    if had_destination:
        os.replace(destination, backup)
    try:
        os.replace(staged, destination)
    except BaseException:
        if had_destination and backup.exists():
            os.replace(backup, destination)
        raise
    if backup.exists():
        try:
            shutil.rmtree(backup)
        except OSError as error:
            log(f"warning: could not remove previous site backup {backup}: {error}")


def build(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target_dir).expanduser().resolve(strict=False)
    if not target.is_dir():
        raise BuildFailure(f"Target directory not found: {target}", 2)
    config_candidate = unresolved_under(target, args.config_file)
    if config_candidate.is_symlink():
        raise BuildFailure(f"Refusing symlinked MkDocs config: {config_candidate}", 2)
    config_file = config_candidate.resolve(strict=False)
    if not config_file.is_file():
        raise BuildFailure(f"MkDocs config not found: {config_file}", 2)
    config = load_raw_config(config_file)
    validate_env_contract(config_file, config)

    docs_value = config.get("docs_dir", "docs")
    if not isinstance(docs_value, (str, os.PathLike)):
        raise BuildFailure("mkdocs.yml `docs_dir` must be a path.", 2)
    docs_candidate = unresolved_under(config_file.parent, docs_value)
    if docs_candidate.is_symlink():
        raise BuildFailure(f"Refusing symlinked docs directory: {docs_candidate}", 2)
    docs_dir = docs_candidate.resolve(strict=False)
    if args.site_dir:
        site_candidate = unresolved_under(target, args.site_dir)
    else:
        site_value = config.get("site_dir", "site")
        if not isinstance(site_value, (str, os.PathLike)):
            raise BuildFailure("mkdocs.yml `site_dir` must be a path.", 2)
        site_candidate = unresolved_under(config_file.parent, site_value)
    if site_candidate.is_symlink():
        raise BuildFailure(f"Refusing symlinked site directory: {site_candidate}", 2)
    site_dir = site_candidate.resolve(strict=False)
    assert_safe_tree(docs_dir, target, site_dir)

    has_i18n, i18n_config = plugin_definition(config, "i18n")
    has_llmstxt, llmstxt_config = plugin_definition(config, "llmstxt")
    default_locale, locales = configured_locales(i18n_config if has_i18n else {})
    nondefault_locales = [locale for locale in locales if locale != default_locale]
    multilingual = has_i18n and bool(nondefault_locales)
    full_output = (
        safe_output_path(llmstxt_config.get("full_output"), "full_output")
        if has_llmstxt
        else None
    )
    site_url = config.get("site_url")
    if has_llmstxt and (not isinstance(site_url, str) or not site_url):
        raise BuildFailure("mkdocs.yml `site_url` is required when llmstxt is configured.", 2)

    two_pass = multilingual and has_llmstxt
    mode = (
        "multilingual-two-pass"
        if two_pass
        else ("multilingual" if multilingual else "monolingual")
    )
    passes = 2 if two_pass else 1
    base_payload: dict[str, Any] = {
        "config_file": str(config_file),
        "default_locale": default_locale,
        "docs_dir": str(docs_dir),
        "locales": locales,
        "mode": mode,
        "passes": passes,
        "site_dir": str(site_dir),
        "target": str(target),
    }
    if args.dry_run:
        emit({**base_payload, "status": "dry-run"})
        return 0

    site_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".mkdocs-site-bootstrap-", dir=site_dir.parent))
    result_payload = base_payload
    try:
        full_docs = temp_dir / "full-docs"
        copy_docs_tree(docs_dir, full_docs)

        if two_pass:
            default_docs = temp_dir / "default-docs"
            default_site = temp_dir / "default-site"
            main_site = temp_dir / "main-site"
            copy_docs_tree(
                docs_dir,
                default_docs,
                nondefault_locales=nondefault_locales,
            )
            run_mkdocs(
                target=target,
                config_file=config_file,
                docs_dir=default_docs,
                site_dir=default_site,
                i18n=False,
                llmstxt=True,
                copy_to_llm=False,
                social=False,
                label="default-language llmstxt pass",
            )
            sidecars, _ = verify_llms_output(
                site_dir=default_site,
                config=config,
                docs_dir=default_docs,
                site_url=site_url,
                full_output=full_output,
                nondefault_locales=nondefault_locales,
            )
            copy_artifacts(
                default_site,
                full_docs,
                full_output=full_output,
                include_sidecars=False,
            )
            run_mkdocs(
                target=target,
                config_file=config_file,
                docs_dir=full_docs,
                site_dir=main_site,
                i18n=True,
                llmstxt=False,
                copy_to_llm=True,
                social=True,
                label="multilingual HTML pass",
            )
            verify_multilingual_html(main_site, nondefault_locales)
            copied = copy_artifacts(
                default_site,
                main_site,
                full_output=full_output,
                include_sidecars=True,
            )
            verify_llms_output(
                site_dir=main_site,
                config=config,
                docs_dir=default_docs,
                site_url=site_url,
                full_output=full_output,
                nondefault_locales=nondefault_locales,
            )
            if copied != len(sidecars):
                raise BuildFailure("Not all generated Markdown sidecars were merged.")
            staged_site = main_site
            sidecar_count = copied
        else:
            staged_site = temp_dir / "main-site"
            run_mkdocs(
                target=target,
                config_file=config_file,
                docs_dir=full_docs,
                site_dir=staged_site,
                i18n=has_i18n,
                llmstxt=has_llmstxt,
                copy_to_llm=True,
                social=True,
                label="strict site pass",
            )
            if multilingual:
                verify_multilingual_html(staged_site, nondefault_locales)
            if has_llmstxt:
                sidecars, _ = verify_llms_output(
                    site_dir=staged_site,
                    config=config,
                    docs_dir=full_docs,
                    site_url=site_url,
                    full_output=full_output,
                    nondefault_locales=nondefault_locales,
                )
                sidecar_count = len(sidecars)
            else:
                sidecar_count = 0

        atomic_replace_tree(staged_site, site_dir)
        result_payload = {
            **base_payload,
            "artifacts": {
                "full_output": str(full_output) if full_output is not None else None,
                "llms": "llms.txt" if has_llmstxt else None,
                "markdown_sidecars": sidecar_count,
            },
            "status": "ok",
        }
        if args.keep_temp:
            result_payload["temp_dir"] = str(temp_dir)
        emit(result_payload)
        return 0
    finally:
        if args.keep_temp:
            log(f"Kept temporary build directory: {temp_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)


def main() -> int:
    try:
        return build(sys.argv[1:])
    except BuildFailure as error:
        log(f"error: {error}")
        emit({"error": str(error), "status": "error"})
        return error.exit_code
    except KeyboardInterrupt:
        log("error: interrupted")
        emit({"error": "interrupted", "status": "error"})
        return 130
    except Exception as error:
        log(f"error: unexpected build failure: {error}")
        emit({"error": str(error), "status": "error"})
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
