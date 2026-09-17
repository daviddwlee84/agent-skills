"""Offline behavioral tests. Repositories, packages and PyPI metadata are synthetic."""
from __future__ import annotations

from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/nt_context.py"
sys.path.insert(0, str(SKILL / "scripts"))
import nt_context as ctx

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"}


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
                          cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class DocsSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nt-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / "cache with spaces"
        self.source = self.root / "upstream"
        self.env = patch.dict(os.environ, {**GIT_ENV, "NAUTILUS_AGENT_REPO_URL": self.source.as_uri()})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.source.mkdir()
        git(self.source, "init", "-q", "-b", "develop")
        git(self.source, "config", "uploadpack.allowFilter", "true")
        write(self.source / "docs/concepts/strategies.md", "# Strategies\n\nsubscribe_quotes\n")
        write(self.source / "docs/tutorials/ema_cross.py", "class EMACross: ...\n")
        write(self.source / "docs/concepts/diagram.png", "binary")
        write(self.source / "examples/backtest/run.py", "print('example')\n")
        write(self.source / "MIGRATION_V2.md", "# Migrate from v1 to v2\n")
        write(self.source / "crates/model/src/lib.rs", "// excluded\n")
        write(self.source / "python/nautilus_trader/__init__.py", "# excluded\n")
        self.commit("first")
        git(self.source, "tag", "-a", "v2.0.0rc5", "-m", "rc5")

    def commit(self, message: str) -> str:
        git(self.source, "add", "-A")
        git(self.source, "commit", "-qm", message)
        return git(self.source, "rev-parse", "HEAD")

    def sync(self, ref="v2.0.0rc5", **kwargs):
        with redirect_stderr(io.StringIO()):
            return ctx.sync_docs(self.cache, ref, **kwargs)

    def test_first_sync_materializes_only_sparse_paths_at_peeled_commit(self):
        result = self.sync()
        self.assertEqual(result["status"], "updated")
        self.assertEqual((result["kind"], result["commit"]), ("tag", git(self.source, "rev-parse", "v2.0.0rc5^{}")))
        base = Path(result["root"])
        found = sorted(str(p.relative_to(base)) for p in base.rglob("*") if p.is_file())
        self.assertEqual(found, ["MIGRATION_V2.md", "docs/concepts/strategies.md", "docs/tutorials/ema_cross.py", "examples/backtest/run.py"])
        self.assertFalse((base / ".git").exists())
        self.assertEqual(result["files"], 4)
        self.assertIsNone(result["root_files"]["RELEASES.md"])
        self.assertEqual(Path(result["root_files"]["MIGRATION_V2.md"]).read_text(), "# Migrate from v1 to v2\n")

    def test_cached_tag_needs_no_network_until_refresh(self):
        first = self.sync()
        with patch.dict(os.environ, {"NAUTILUS_AGENT_REPO_URL": (self.root / "missing").as_uri()}):
            again = self.sync()
            self.assertEqual((again["status"], again["root"]), ("cached", first["root"]))
            stale = self.sync(refresh=True)
        self.assertEqual(stale["status"], "stale")
        self.assertIn("git ls-remote failed", stale["warning"])
        self.assertEqual(self.sync(refresh=True)["status"], "unchanged")

    def test_branch_ttl_unchanged_then_updated_keeps_previous_generation(self):
        first = self.sync("develop")
        self.assertEqual(self.sync("develop")["status"], "cached")
        manifest_path = Path(first["manifest"])
        manifest = json.loads(manifest_path.read_text())
        manifest["checked_at"] = time.time() - ctx.TTL - 1
        manifest_path.write_text(json.dumps(manifest))
        self.assertEqual(self.sync("develop")["status"], "unchanged")
        write(self.source / "docs/concepts/strategies.md", "# Strategies\n\nchanged\n")
        head = self.commit("second")
        second = self.sync("develop", refresh=True)
        self.assertEqual((second["status"], second["commit"]), ("updated", head))
        self.assertIn("changed", (Path(second["docs_dir"]) / "concepts/strategies.md").read_text())
        self.assertTrue(Path(first["root"]).is_dir(), "previous generation must survive one swap")
        write(self.source / "docs/concepts/strategies.md", "# Strategies\n\nthird\n")
        self.commit("third")
        third = self.sync("develop", refresh=True)
        self.assertFalse(Path(first["root"]).exists(), "older generations are pruned")
        self.assertTrue(Path(second["root"]).is_dir())
        self.assertEqual(third["status"], "updated")

    def test_failures_without_cache_and_offline_are_actionable(self):
        with patch.dict(os.environ, {"NAUTILUS_AGENT_REPO_URL": (self.root / "missing").as_uri()}):
            with self.assertRaises(ctx.ContextError) as external:
                self.sync()
        self.assertEqual(external.exception.code, 3)
        with self.assertRaises(ctx.ContextError) as offline:
            self.sync(offline=True)
        self.assertEqual(offline.exception.code, 2)
        with self.assertRaisesRegex(ctx.ContextError, "not found upstream") as missing:
            self.sync("v9.9.9")
        self.assertEqual(missing.exception.code, 2)
        self.assertFalse((self.cache / "refs/v9.9.9/generations").exists() and any((self.cache / "refs/v9.9.9/generations").iterdir()))
        self.sync()
        self.assertEqual(self.sync(offline=True)["status"], "offline")

    def test_ref_validation_and_version_normalization(self):
        self.assertEqual(ctx.normalize_ref("2.0.0rc5"), "v2.0.0rc5")
        self.assertEqual(ctx.normalize_ref("develop_v1"), "develop_v1")
        for bad in ("../../elsewhere", "-u", "a/..", "latest/", ""):
            with self.assertRaises(ctx.ContextError):
                ctx.normalize_ref(bad)
        self.assertTrue(ctx.is_tag("v1.231.0"))
        self.assertFalse(ctx.is_tag("develop"))

    def test_dry_run_writes_nothing_and_cli_has_json_stdout(self):
        result = self.sync(dry_run=True)
        self.assertEqual((result["status"], result["action"]), ("dry_run", "clone"))
        self.assertFalse(self.cache.exists())
        proc = subprocess.run([sys.executable, str(SCRIPT), "docs", "--ref", "2.0.0rc5", "--cache-dir", str(self.cache)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "updated")
        self.assertEqual(self.sync(dry_run=True)["action"], "none")
        proc = subprocess.run([sys.executable, str(SCRIPT), "docs", "--ref", "v2.0.0rc5", "--offline", "--refresh"], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (2, ""))

    def test_cross_process_lock(self):
        with ctx.ref_lock(self.cache / "refs/v2.0.0rc5"):
            proc = subprocess.run([sys.executable, str(SCRIPT), "docs", "--ref", "v2.0.0rc5", "--cache-dir", str(self.cache)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("Another process", proc.stderr)

    def test_corrupt_manifest_is_not_trusted(self):
        first = self.sync()
        Path(first["manifest"]).write_text("not JSON")
        self.assertEqual(self.sync()["status"], "updated")


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nt-env-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def test_xdg_precedence(self):
        with patch.object(Path, "home", return_value=self.project):
            for value in ("", "relative/cache"):
                with patch.dict(os.environ, {"XDG_CACHE_HOME": value}), redirect_stderr(io.StringIO()):
                    self.assertEqual(ctx.cache_root(), self.project / ".cache/nautilus-trader-agent")
            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.project / "xdg with spaces")}):
                self.assertEqual(ctx.cache_root(), self.project / "xdg with spaces/nautilus-trader-agent")
                self.assertEqual(ctx.cache_root("./override"), Path.cwd() / "override")

    def fake_package(self, version: str, core: str) -> None:
        package = self.project / "nautilus_trader"
        write(package / "__init__.py", f'print("incidental output")\n__version__ = "{version}"\n')
        if core == "pyo3":
            write(package / "_libnautilus.cpython-312-darwin.so", "")
        else:
            write(package / "core/nautilus_pyo3.cpython-312-darwin.so", "")
            write(package / "core/uuid.pxd", "")

    def test_probe_detects_generation_native_core_and_venv(self):
        for version, core, generation in (("1.231.0", "cython", "v1"), ("2.0.0rc5", "pyo3", "v2")):
            with self.subTest(version=version):
                self.fake_package(version, core)
                probe = ctx.probe_python(Path(sys.executable), self.project)
                package = probe["package"]
                self.assertEqual((package["version"], package["native_core"], package["generation"], package["importable"]), (version, core, generation, True))
                for path in (self.project / "nautilus_trader").rglob("*"):
                    if path.is_file() and path.suffix in (".so", ".pxd"):
                        path.unlink()
        python = self.project / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        self.assertEqual(ctx.python_path(self.project, None), python)
        with self.assertRaises(ctx.ContextError):
            ctx.python_path(self.project, str(self.project / "missing/python"))

    def test_pins_locks_ranges_and_crates(self):
        write(self.project / "uv.lock", 'version = 1\n[[package]]\nname = "nautilus-trader"\nversion = "2.0.0rc5"\n')
        write(self.project / "pyproject.toml", '[project]\nname = "x"\ndependencies = ["nautilus_trader[visualization]>=2.0.0rc1 ; python_version >= \'3.12\'", "nautilus-trader-extras==9"]\n[tool.uv]\nprerelease = "allow"\n')
        write(self.project / "requirements-live.txt", "nautilus_trader==1.231.*\nnautilus-trader<2\n")
        write(self.project / "Cargo.toml", '[package]\nname = "bot"\n[dependencies]\nnautilus-model = { version = "0.64", features = ["high-precision"] }\nnautilus-live = { git = "https://example.invalid/nt.git", branch = "develop" }\nserde = "1"\n')
        pins, crates, prerelease = ctx.pins_and_crates(self.project)
        self.assertEqual(pins[0], {"source": "uv.lock", "spec": "==2.0.0rc5", "version": "2.0.0rc5", "exact": True, "generation": "v2", "locked": True})
        self.assertEqual([(p["source"], p["exact"], p["generation"]) for p in pins[1:]],
                         [("pyproject.toml", False, "v2"), ("requirements-live.txt", False, "v1"), ("requirements-live.txt", False, "v1")])
        self.assertEqual(prerelease, "allow")
        self.assertEqual({c["name"]: (c["version"], c["branch"]) for c in crates}, {"nautilus-model": ("0.64", None), "nautilus-live": (None, "develop")})
        write(self.project / "pyproject.toml", '[tool.poetry.dependencies]\nnautilus-trader = "1.231.0"\n')
        pins, _, _ = ctx.pins_and_crates(self.project)
        poetry = [p for p in pins if "poetry" in p["source"]][0]
        self.assertEqual((poetry["spec"], poetry["exact"], poetry["generation"]), ("^1.231.0", False, "v1"))
        write(self.project / "Cargo.lock", "not = [toml")
        with self.assertRaises(ctx.ContextError) as broken:
            ctx.pins_and_crates(self.project)
        self.assertEqual(broken.exception.code, 2)

    def test_marker_scan_requires_package_import_and_whole_identifiers(self):
        write(self.project / "live_v1.py", "from nautilus_trader.live.node import TradingNode\nclass S:\n    def on_quote_tick(self, tick): ...\n")
        write(self.project / "v2.py", "from nautilus_trader.config import DataActorConfig\nfrom nautilus_trader.live import LiveNode\nnode = LiveNode.builder('n', 't', 'LIVE')\n")
        write(self.project / "unrelated.py", "class Feed:\n    def on_quote(self, quote): ...\n    def on_quote_tick(self): ...\n")
        write(self.project / ".venv/lib/nautilus_trader/live/node.py", "from nautilus_trader.live.node import TradingNode\n")
        write(self.project / "broken.py", "import nautilus_trader\ndef (:\n")
        scan = ctx.marker_scan(self.project)
        self.assertEqual(sorted(scan["files_importing"]), ["live_v1.py", "v2.py"])
        self.assertEqual({m["name"] for m in scan["samples"]["v1"]}, {"nautilus_trader.live.node", "TradingNode", "on_quote_tick"})
        self.assertEqual({m["name"] for m in scan["samples"]["v2"]}, {"DataActorConfig", "LiveNode"})
        self.assertNotIn("ActorConfig", {m["name"] for m in scan["samples"]["v1"]})
        self.assertTrue(scan["heuristic"])
        for index in range(4):
            write(self.project / f"many/f{index}.py", "import nautilus_trader\n")
        self.assertTrue(ctx.marker_scan(self.project, limit=3)["scan_truncated"])

    def test_recommendation_precedence_conflicts_and_versions(self):
        empty = {"counts": {"v1": 0, "v2": 0}, "scan_truncated": False}
        v1_code = {"counts": {"v1": 3, "v2": 0}, "scan_truncated": False}
        mixed = {"counts": {"v1": 1, "v2": 1}, "scan_truncated": False}
        pypi = {"latest_by_generation": {"v1": "1.231.0", "v2": "2.0.0rc5"}}
        installed_v2 = {"importable": True, "generation": "v2", "version": "2.0.0.dev20260916+123"}
        lock_v1 = [{"source": "uv.lock", "version": "1.231.0", "exact": True, "generation": "v1"}]

        result = ctx.recommend("auto", lock_v1, empty, installed_v2, pypi)
        self.assertEqual((result["generation"], result["docs_ref"], result["approximate"]), ("v1", "v1.231.0", False))
        self.assertEqual(result["conflicts"], ["installed package: v2"])

        result = ctx.recommend("auto", [], v1_code, {}, pypi)
        self.assertEqual((result["generation"], result["version"], result["docs_ref"], result["approximate"]), ("v1", "1.231.0", "v1.231.0", True))

        result = ctx.recommend("auto", [], empty, installed_v2, pypi)
        self.assertEqual((result["docs_ref"], result["approximate"], result["release_candidate"]), ("develop", True, False))

        result = ctx.recommend("auto", [], mixed, installed_v2, pypi)
        self.assertIsNone(result["generation"])
        self.assertIsNone(result["docs_ref"])

        result = ctx.recommend("v2", lock_v1, v1_code, {}, pypi)
        self.assertEqual((result["generation"], result["docs_ref"], result["release_candidate"]), ("v2", "v2.0.0rc5", True))
        self.assertEqual(result["conflicts"], ["project pins: v1", "code markers: v1"])

        result = ctx.recommend("auto", [], {**empty, "scan_truncated": True}, {}, {"status": "skipped"})
        self.assertEqual((result["generation"], result["new_project"], result["docs_ref"]), ("v2", True, "develop"))
        self.assertIn("truncated", result["conflicts"][0])

    def test_version_refs(self):
        cases = {"1.231.0": ("v1.231.0", False), "2.0.0rc5": ("v2.0.0rc5", False), "2.0.0rc6.dev20260916+9001": ("develop", True),
                 "2.0.0rc6.dev20260916": ("develop", True), "1.230.0a20260601": ("develop_v1", True), "not-a-version": (None, True)}
        for version, expected in cases.items():
            self.assertEqual(ctx.ref_for_version(version), expected, version)

    def test_pypi_prerelease_state(self):
        def status(releases):
            path = self.project / "pypi.json"
            path.write_text(json.dumps({"releases": releases}))
            with patch.dict(os.environ, {"NAUTILUS_AGENT_PYPI_URL": path.as_uri()}):
                return ctx.pypi_status(False)

        file = [{"yanked": False}]
        current = status({"1.230.0": file, "1.231.0": file, "2.0.0rc4": file, "2.0.0rc5": file, "2.0.0rc6": [{"yanked": True}], "1.232.0": []})
        self.assertEqual((current["stable"], current["prerelease"], current["pre_flag_required"]), ("1.231.0", "2.0.0rc5", True))
        self.assertEqual(current["latest_by_generation"], {"v1": "1.231.0", "v2": "2.0.0rc5"})
        final = status({"1.231.0": file, "2.0.0rc5": file, "2.0.0": file})
        self.assertEqual((final["stable"], final["prerelease"], final["pre_flag_required"]), ("2.0.0", None, False))
        self.assertEqual(ctx.pypi_status(True)["status"], "skipped")
        with patch.dict(os.environ, {"NAUTILUS_AGENT_PYPI_URL": (self.project / "missing.json").as_uri()}):
            self.assertEqual(ctx.pypi_status(False)["status"], "unknown")

    def test_doctor_cli_offline_json(self):
        self.fake_package("1.231.0", "cython")
        write(self.project / "strategy.py", "from nautilus_trader.trading.strategy import Strategy\nclass S(Strategy):\n    def on_quote_tick(self, tick): ...\n")
        proc = subprocess.run([sys.executable, str(SCRIPT), "doctor", "--project", str(self.project), "--python", sys.executable, "--offline", "--cache-dir", str(self.project / "cache")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual((report["pypi"]["status"], report["recommendation"]["generation"], report["recommendation"]["docs_ref"]), ("skipped", "v1", "v1.231.0"))
        self.assertEqual(report["cached_refs"], [])
        proc = subprocess.run([sys.executable, str(SCRIPT), "doctor", "--project", str(self.project / "missing")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_marketplace_group_membership(self):
        repo = SKILL.parents[2]
        manifest = json.loads((repo / "skills/.claude-plugin/marketplace.json").read_text())
        groups = {x["name"]: x for x in manifest["plugins"]}
        self.assertIn("./local/nautilus-trader", groups["quantitative-finance"]["skills"])


if __name__ == "__main__":
    unittest.main()
