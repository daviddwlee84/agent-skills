"""Regression tests for explicit sourced-only libraries; lint never runs them.

Run: uv run --extra dev pytest skills/local/skill-author/tests/ -q
Uses both PATH Bash and /bin/bash when distinct (including macOS Bash 3.2).
"""
from __future__ import annotations

import json
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
LINTER = SKILL_ROOT / "scripts/lint-skill.sh"
BASHES = list(dict.fromkeys(
    str(Path(p).resolve()) for p in (shutil.which("bash"), "/bin/bash")
    if p and Path(p).is_file()
))
MARKER = "# skill-lint: sourced-only\n"


@pytest.fixture(params=BASHES)
def bash(request):
    return request.param


@pytest.fixture
def sample(tmp_path):
    root = tmp_path / "sample-skill"
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text(
        "---\nname: sample-skill\n"
        "description: 'Use when testing shell script hygiene in a sample skill, "
        "including explicit sourced-only libraries, regular CLI entrypoints, "
        "and checks that never execute inspected files.'\n---\n# Sample\n"
    )
    return root


def lint(bash, root):
    result = subprocess.run(
        [bash, str(LINTER), "--strict", "--json", str(root)],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, json.loads(result.stdout.splitlines()[-1])


def script(sample, content, executable=False):
    path = sample / "scripts/example.sh"
    path.write_text(content)
    path.chmod(0o755 if executable else 0o644)
    return path


def test_sourced_library_passes_without_executing(bash, sample, tmp_path):
    sentinel = tmp_path / "must-not-exist"
    script(sample, "# shellcheck shell=bash\n\n" + MARKER
           + f"touch {shlex.quote(str(sentinel))}\nhelper() {{ :; }}\n")
    code, report = lint(bash, sample)
    assert code == 0
    assert report["errors"] == report["warnings"] == 0
    assert not sentinel.exists(), "lint must parse, never source or run a library"


def test_unmarked_file_still_requires_cli_contract(bash, sample):
    # Describing a library in prose or omitting +x is not an opt-out.
    script(sample, "# Sourced library, not executed directly.\nhelper() { :; }\n")
    code, report = lint(bash, sample)
    assert code == 3
    assert report["errors"] == 2
    assert report["warnings"] == 1


def test_marker_after_shell_code_does_not_opt_out(bash, sample):
    script(sample, "helper() {\n" + MARKER + "  :\n}\n")
    code, report = lint(bash, sample)
    assert code == 3
    assert report["errors"] == 2


def test_executable_cannot_claim_sourced_only(bash, sample):
    script(sample, "#!/usr/bin/env bash\n" + MARKER + "# --help\n:", executable=True)
    code, report = lint(bash, sample)
    assert code == 3
    assert any("marked sourced-only but executable" in m for m in report["error_messages"])


def test_sourced_library_syntax_is_checked(bash, sample):
    script(sample, MARKER + "helper() {\n")
    code, report = lint(bash, sample)
    assert code == 3
    assert any("invalid Bash syntax" in m for m in report["error_messages"])


def test_regular_cli_still_passes(bash, sample):
    script(sample, '#!/usr/bin/env bash\ncase "${1:-}" in --help) exit 0 ;; esac\n', executable=True)
    code, report = lint(bash, sample)
    assert code == 0
    assert report["errors"] == report["warnings"] == 0


def test_regular_cli_without_help_fails_strict(bash, sample):
    script(sample, "#!/usr/bin/env bash\n:\n", executable=True)
    code, report = lint(bash, sample)
    assert code == 3
    assert report["warnings"] == 1


def test_real_forge_skill_passes_strict(bash):
    code, report = lint(bash, SKILL_ROOT.parent / "forge-native-dev")
    assert code == 0, report
    assert report["errors"] == report["warnings"] == 0
