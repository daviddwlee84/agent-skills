"""Offline behavioral tests. All document content is synthetic."""
from __future__ import annotations

from contextlib import redirect_stderr
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import vbt_context as ctx
import vbt_mcp as mcp


FAKE_GH = '''#!/usr/bin/env python3
import json, os, pathlib, shutil, sys
root = pathlib.Path(os.environ["FAKE_VBT_REMOTE"])
with (root / "calls").open("a") as f: f.write(json.dumps(sys.argv[1:]) + "\\n")
if os.environ.get("FAKE_VBT_FAILURE"):
    print(os.environ["FAKE_VBT_FAILURE"], file=sys.stderr)
    sys.exit(1)
args = sys.argv[1:]
if args[0] == "api":
    if args[1] == "repos/polakowo/vectorbt.pro":
        print(json.dumps({"full_name": "polakowo/vectorbt.pro"}))
    else:
        print((root / "metadata.json").read_text())
elif args[:2] == ["release", "download"]:
    name = args[args.index("--pattern") + 1]
    target = args[args.index("--output") + 1]
    shutil.copyfile(root / name, target)
else:
    sys.exit(2)
'''


def fixtures(label="original"):
    url = "https://members.example.invalid/cookbook/test/"
    return {
        "pages": [
            {"link": url, "name": "Synthetic tutorial", "type": "page", "parent": None, "children": [url + "#first", url + "#second", url + "child/"], "content": label},
            {"link": url + "#second", "name": "Second", "type": "heading 2", "parent": url, "children": [], "content": "Second content"},
            {"link": url + "#first", "name": "First", "type": "heading 2", "parent": url, "children": [], "content": "繁體中文\n\n```python\nvalue = 42\n```"},
            {"link": url + "child/", "name": "Child page", "type": "page", "parent": url, "children": [], "content": "Child-only body"},
        ],
        "examples": [{"link": url + "#first", "title": "Synthetic example", "description": label, "content": "```python\nvalue = 42\n```", "verified": True}],
        "messages": [{"link": "https://discord.example.invalid/channels/1/2/3", "reference": "2", "channel": "synthetic", "content": "Question\nAnswer"}],
    }


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vbt-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote"
        self.remote.mkdir()
        self.cache = self.root / "cache with spaces"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.env = patch.dict(os.environ, {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"], "FAKE_VBT_REMOTE": str(self.remote), "FAKE_VBT_FAILURE": ""})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.remote_write()

    def remote_write(self, data=None, release="v2026.9.5", revision=1, digest=True):
        assets = []
        for i, (name, items) in enumerate((data or fixtures()).items()):
            blob = gzip.compress(json.dumps(items, ensure_ascii=False).encode(), mtime=0)
            filename = name + ".json.gz"
            (self.remote / filename).write_bytes(blob)
            assets.append({"name": filename, "id": revision * 10 + i, "updated_at": str(revision), "size": len(blob), "digest": "sha256:" + hashlib.sha256(blob).hexdigest() if digest else None})
        (self.remote / "metadata.json").write_text(json.dumps({"tag_name": release, "assets": assets}))

    def sync(self, **kwargs):
        return ctx.sync_pro(self.cache, "v2026.9.5", {"pages", "examples"}, **kwargs)

    def test_initial_render_preserves_hierarchy_code_and_lines(self):
        result = self.sync()
        self.assertEqual(result["status"], "updated")
        rows = [json.loads(x) for x in Path(result["index"]).read_text().splitlines()]
        root = Path(result["index"]).parent
        first = next(x for x in rows if x["asset"] == "pages" and x["title"] == "First")
        text = (root / first["path"]).read_text()
        self.assertIn("繁體中文\n\n```python\nvalue = 42\n```", text)
        self.assertLess(text.index("## First"), text.index("## Second"))
        self.assertNotIn("Child-only body", text)
        self.assertEqual(text.splitlines()[first["line"] - 1], "## First")
        self.assertTrue(all(row["release"] == "v2026.9.5" for row in rows))
        example = next(x for x in rows if x["asset"] == "examples")
        self.assertTrue(example["verified"])
        self.assertIn("not a local test result", (root / example["path"]).read_text())

    def test_ttl_refresh_and_same_tag_replacement(self):
        first = self.sync()
        calls = (self.remote / "calls").read_text()
        self.assertEqual(self.sync()["status"], "cached")
        self.assertEqual((self.remote / "calls").read_text(), calls)
        self.assertEqual(self.sync(refresh=True)["status"], "unchanged")
        self.assertEqual((self.remote / "calls").read_text().count('"download"'), 2)
        data = fixtures("updated content")
        data["pages"] = data["pages"][:3]
        self.remote_write(data, revision=2)
        changed = self.sync(refresh=True)
        self.assertNotEqual(first["markdown_dir"], changed["markdown_dir"])
        self.assertEqual(len(list((Path(changed["markdown_dir"]) / "pages").glob("*.md"))), 1)
        self.assertTrue(Path(first["markdown_dir"]).is_dir())

    def test_offline_stale_and_auth_states(self):
        with self.assertRaises(ctx.ContextError):
            self.sync(offline=True)
        self.sync()
        with patch.dict(os.environ, {"FAKE_VBT_FAILURE": "HTTP 404"}):
            self.assertEqual(ctx.pro_access()["status"], "denied")
            self.assertEqual(self.sync(offline=True)["status"], "offline")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(self.sync(refresh=True)["status"], "stale")
        with patch.dict(os.environ, {"FAKE_VBT_FAILURE": "network disconnected"}):
            self.assertEqual(ctx.pro_access()["status"], "unknown")
        self.assertEqual(ctx.pro_access(True)["status"], "unknown")
        self.assertEqual(ctx.pro_access()["status"], "allowed")

    def test_checksum_and_json_errors_preserve_previous_manifest(self):
        result = self.sync()
        path = Path(result["manifest"])
        original = path.read_bytes()
        self.remote_write(revision=2)
        (self.remote / "pages.json.gz").write_bytes(b"bad")
        with self.assertRaises(ctx.ContextError) as error:
            self.sync(refresh=True)
        self.assertEqual(error.exception.code, 4)
        self.assertEqual(path.read_bytes(), original)
        self.remote_write({"pages": [{"wrong": "schema"}], "examples": fixtures()["examples"]}, revision=3)
        with self.assertRaises(ctx.ContextError):
            self.sync(refresh=True)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(list(path.parent.glob("generations/.staging-*")))

    def test_missing_digest_and_local_corruption(self):
        self.remote_write(digest=False)
        result = self.sync()
        manifest = json.loads(Path(result["manifest"]).read_text())
        self.assertFalse(manifest["assets"]["pages"]["remote_checksum_verified"])
        (Path(result["raw_dir"]) / "pages.json.gz").write_bytes(b"corrupt")
        with self.assertRaises(ctx.ContextError):
            self.sync(offline=True)
        self.assertEqual(self.sync()["status"], "updated")

    def test_messages_added_and_refreshed_with_default_sync(self):
        self.sync()
        result = ctx.sync_pro(self.cache, "v2026.9.5", set(ctx.ASSETS))
        messages = Path(result["markdown_dir"]) / "messages.jsonl"
        self.assertEqual(json.loads(messages.read_text())["reference"], "2")
        self.remote_write(revision=2)
        refreshed = self.sync(refresh=True)
        self.assertIn("messages", refreshed["assets"])

    def test_mcp_uses_paths_and_isolates_native_indexes_by_generation(self):
        result = ctx.sync_pro(self.cache, "v2026.9.5", set(ctx.ASSETS))
        settings = {}
        fake = SimpleNamespace(version="2026.9.5", settings=SimpleNamespace(set=lambda key, value: settings.__setitem__(key, value)))
        with patch.dict(sys.modules, {"vectorbtpro": fake}):
            mcp.load_pro_cache(self.cache)
        self.assertEqual(settings["knowledge.assets.pages.assets_dir"], Path(result["raw_dir"]))
        self.assertTrue(settings["knowledge.cache_dir"].is_relative_to(self.cache))
        self.assertEqual(settings["knowledge.cache_dir"].name, Path(result["raw_dir"]).parent.name)
        fake.version = "2026.9.6"
        with patch.dict(sys.modules, {"vectorbtpro": fake}), self.assertRaises(ctx.ContextError):
            mcp.load_pro_cache(self.cache)

    def test_version_isolation_and_wrong_release(self):
        first = self.sync()
        with self.assertRaises(ctx.ContextError):
            ctx.sync_pro(self.cache, "v2026.9.6", {"pages"})
        self.remote_write(release="v2026.9.6")
        second = ctx.sync_pro(self.cache, "v2026.9.6", {"pages"})
        self.assertNotEqual(first["raw_dir"], second["raw_dir"])
        self.assertTrue(Path(first["raw_dir"]).is_dir())
        with self.assertRaises(ctx.ContextError):
            ctx.release_tag("../../elsewhere")

    def test_dry_run_writes_nothing_and_cli_has_json_stdout(self):
        result = self.sync(dry_run=True)
        self.assertEqual(result["status"], "dry_run")
        self.assertFalse(self.cache.exists())
        proc = subprocess.run([sys.executable, str(SKILL / "scripts/vbt_context.py"), "sync-pro", "--release", "v2026.9.5", "--cache-dir", str(self.cache)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "updated")

    def test_cross_process_lock(self):
        with ctx.release_lock(self.cache / "pro/v2026.9.5"):
            proc = subprocess.run([sys.executable, str(SKILL / "scripts/vbt_context.py"), "sync-pro", "--release", "v2026.9.5", "--cache-dir", str(self.cache)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("Another process", proc.stderr)

    def test_missing_optional_asset_and_cycle_are_actionable(self):
        self.remote_write({"pages": fixtures()["pages"]})
        with self.assertRaisesRegex(ctx.ContextError, "--assets"):
            self.sync()
        result = ctx.sync_pro(self.cache, "v2026.9.5", {"pages"})
        self.assertEqual(result["assets"], ["pages"])
        nodes = [{"link": "a", "parent": "b", "type": "heading 2", "content": "a"}, {"link": "b", "parent": "a", "type": "heading 2", "content": "b"}]
        self.remote_write({"pages": nodes}, revision=2)
        with self.assertRaisesRegex(ctx.ContextError, "Cycle"):
            ctx.sync_pro(self.cache, "v2026.9.5", {"pages"}, refresh=True)


class EnvironmentTests(unittest.TestCase):
    def test_xdg_precedence_and_shared_mcp_resolver(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            with patch.object(Path, "home", return_value=home):
                for value in ("", "relative/cache"):
                    with patch.dict(os.environ, {"XDG_CACHE_HOME": value}), redirect_stderr(io.StringIO()):
                        self.assertEqual(ctx.cache_root(), home / ".cache/vectorbt-agent")
                with patch.dict(os.environ, {"XDG_CACHE_HOME": str(home / "xdg with spaces")}):
                    self.assertEqual(ctx.cache_root(), home / "xdg with spaces/vectorbt-agent")
                    self.assertEqual(ctx.cache_root("./override"), Path.cwd() / "override")
                    self.assertEqual(mcp.cache_root(), ctx.cache_root())
                with patch.dict(os.environ):
                    os.environ.pop("XDG_CACHE_HOME", None)
                    self.assertEqual(ctx.cache_root(), home / ".cache/vectorbt-agent")

    def test_existing_edition_wins_and_new_pro_is_preferred(self):
        both = {"vectorbt": {"importable": True}, "vectorbtpro": {"importable": True}}
        self.assertEqual(ctx.choose_edition("auto", {"editions": ["oss"]}, both, "allowed")["edition"], "oss")
        self.assertEqual(ctx.choose_edition("auto", {"editions": ["pro"]}, both, "unknown")["edition"], "pro")
        self.assertEqual(ctx.choose_edition("auto", {"editions": []}, {}, "allowed")["edition"], "pro")
        self.assertEqual(ctx.choose_edition("auto", {"editions": []}, {}, "denied")["edition"], "oss")
        self.assertEqual(ctx.choose_edition("oss", {"editions": ["pro"]}, both, "allowed")["edition"], "oss")
        self.assertEqual(ctx.choose_edition("auto", {"editions": []}, both, "allowed")["edition"], "pro")
        self.assertIsNone(ctx.choose_edition("auto", {"editions": []}, both, "unknown")["edition"])

    def test_probe_actual_import_version_and_venv_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            package = project / "vectorbt"
            package.mkdir()
            (package / "__init__.py").write_text('print("incidental output")\n__version__ = "1.2.3"\n')
            (project / "strategy.py").write_text('import vectorbt as vbt\n# import vectorbtpro as vbt\n')
            evidence = ctx.project_evidence(project)
            self.assertEqual(evidence["editions"], ["oss"])
            python = project / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.symlink_to(sys.executable)
            self.assertEqual(ctx.python_path(project, None), python)
            probe = ctx.probe_python(Path(sys.executable), project)
            self.assertEqual(probe["packages"]["vectorbt"]["version"], "1.2.3")
            self.assertEqual(Path(probe["packages"]["vectorbt"]["origin"]).resolve(), (package / "__init__.py").resolve())


class MCPConfigTests(unittest.TestCase):
    def test_tool_failure_never_counts_as_verified(self):
        for flag in ("is_error", "isError"):
            result = SimpleNamespace(content=[SimpleNamespace(type="text", text="Tool failed")], **{flag: True})
            with self.assertRaises(ctx.ContextError):
                mcp.tool_text("get_page", result)
        with self.assertRaises(ctx.ContextError):
            mcp.tool_text("search", SimpleNamespace(content=[SimpleNamespace(type="text", text="No results found")]))

    def test_codex_preview_apply_preserve_idempotence_and_conflict(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            path = project / ".codex/config.toml"
            path.parent.mkdir()
            original = '# existing comment\nmodel = "custom"\n[mcp_servers.other]\ncommand = "other"\n'
            path.write_text(original)
            root = project / "cache with spaces"
            result = mcp.config(project, Path(sys.executable), root, "codex", False)
            self.assertEqual(result["status"], "preview")
            self.assertEqual(path.read_text(), original)
            self.assertFalse(result["client_loaded"])
            result = mcp.config(project, Path(sys.executable), root, "codex", True)
            parsed = tomllib.loads(path.read_text())
            self.assertEqual(parsed["model"], "custom")
            self.assertEqual(parsed["mcp_servers"]["other"], {"command": "other"})
            self.assertTrue(path.read_text().startswith('# existing comment'))
            self.assertEqual(mcp.config(project, Path(sys.executable), root, "codex", True)["status"], "unchanged")
            before = path.read_bytes()
            with self.assertRaisesRegex(ctx.ContextError, "already exists"):
                mcp.config(project, Path(sys.executable), project / "different", "codex", True)
            self.assertEqual(path.read_bytes(), before)

    def test_claude_preserves_unrelated_fields_and_has_no_secret_env(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            path = project / ".mcp.json"
            path.write_text(json.dumps({"custom": 42, "mcpServers": {"other": {"command": "other", "env": {"SETTING": "preserved"}}}}))
            result = mcp.config(project, Path(sys.executable), project / "cache", "claude", True)
            parsed = json.loads(path.read_text())
            self.assertEqual(parsed["custom"], 42)
            self.assertEqual(parsed["mcpServers"]["other"]["env"]["SETTING"], "preserved")
            self.assertNotIn("env", parsed["mcpServers"]["vectorbtpro"])
            self.assertEqual(result["scope"], "project")

    def test_invalid_existing_config_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            path = project / ".mcp.json"
            path.write_text("not JSON")
            with self.assertRaises(ctx.ContextError):
                mcp.config(project, Path(sys.executable), project / "cache", "claude", True)
            self.assertEqual(path.read_text(), "not JSON")

    def test_marketplace_group_is_exact_and_disjoint(self):
        repo = SKILL.parents[2]
        manifest = json.loads((repo / "skills/.claude-plugin/marketplace.json").read_text())
        groups = {x["name"]: x for x in manifest["plugins"]}
        expected = {"./local/vectorbt", "./local/quantatitive-factor-researcher", "./local/nautilus-trader"}
        self.assertEqual(set(groups["quantitative-finance"]["skills"]), expected)
        self.assertTrue(expected.isdisjoint(groups["04-ml-workflow"]["skills"]))


if __name__ == "__main__":
    unittest.main()
