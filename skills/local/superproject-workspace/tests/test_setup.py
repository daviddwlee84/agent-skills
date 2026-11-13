"""Setup tests: `new`, `add`, and checkout-state handling in `init`/`status`/`audit`.

Run: python3 -m unittest discover -s skills/local/superproject-workspace/tests -p 'test_setup.py' -v
"""

from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path

from test_superproject import BaseFixture, Fixture, sh


def head_or_none(repo: Path) -> str | None:
    p = subprocess.run(["git", "rev-parse", "-q", "--verify", "HEAD"], cwd=repo, capture_output=True, text=True)
    return p.stdout.strip() or None


def gm(repo: Path, key: str) -> str:
    return sh("git", "config", "-f", ".gitmodules", "--get", key, cwd=repo, check=False)


class TestNew(BaseFixture):
    def test_new_creates_marker_and_scaffold(self) -> None:
        ws = self.tmp / "ws"
        res = self.json_cli("new", str(ws), cwd=self.tmp)
        self.assertEqual(Path(res["root"]), ws.resolve())
        self.assertEqual(res["mode"], "submodule")
        self.assertTrue((ws / ".git").is_dir())
        self.assertEqual(sh("git", "config", "-f", ".superproject", "workspace.mode", cwd=ws), "submodule")
        self.assertIn("superproject-workspace:agent-guidance", (ws / "AGENTS.md").read_text())
        self.assertIn("superproject-workspace:begin", (ws / "justfile").read_text())
        self.assertIn(".worktrees/", (ws / ".gitignore").read_text())
        self.assertEqual(sh("git", "config", "--local", "push.recurseSubmodules", cwd=ws), "check")
        self.assertIsNone(head_or_none(ws))  # nothing committed
        self.assertEqual(sh("git", "diff", "--cached", "--name-only", cwd=ws), "")  # nothing staged

        # The marker alone makes it a root: from inside, and via $SUPERPROJECT_ROOT from elsewhere.
        status = self.json_cli("status", cwd=ws)
        self.assertEqual(status["submodules"], [])
        os.environ["SUPERPROJECT_ROOT"] = str(ws)
        self.assertEqual(Path(self.json_cli("status", cwd=self.tmp)["root"]), ws.resolve())
        os.environ.pop("SUPERPROJECT_ROOT")

        findings = {f["code"]: f for f in self.json_cli("audit", cwd=ws)["findings"]}  # a fresh root passes
        self.assertEqual(findings["no-submodules"]["level"], "info")
        self.assertNotIn("agents-block", findings)
        self.assertNotIn("worktrees-not-ignored", findings)

    def test_audit_no_children_is_info_for_marker_error_for_gitmodules(self) -> None:
        ws = self.tmp / "ws"
        self.run_cli("new", str(ws), cwd=self.tmp)
        f = next(x for x in self.json_cli("audit", cwd=ws)["findings"] if x["code"] == "no-submodules")
        self.assertEqual((f["level"], f["subject"]), ("info", ".superproject"))

        # A .gitmodules that declares nothing usable (no path) is broken, marker or not.
        (ws / ".gitmodules").write_text('[submodule "ghost"]\n\turl = https://example.com/ghost.git\n')
        f = next(x for x in self.json_cli("audit", cwd=ws, expect=1)["findings"] if x["code"] == "no-submodules")
        self.assertEqual((f["level"], f["subject"]), ("error", ".gitmodules"))

        legacy = self.tmp / "legacy"
        legacy.mkdir()
        sh("git", "init", "-q", cwd=legacy)
        (legacy / ".gitmodules").write_text("")
        f = next(x for x in self.json_cli("audit", cwd=legacy, expect=1)["findings"] if x["code"] == "no-submodules")
        self.assertEqual(f["level"], "error")

    def test_new_dry_run_writes_nothing(self) -> None:
        ws = self.tmp / "ws"
        res = self.json_cli("new", str(ws), "--dry-run", cwd=self.tmp)
        self.assertTrue(res["dry_run"])
        self.assertIn("git init", [a["detail"] for a in res["actions"]])
        self.assertFalse(ws.exists())

        empty = self.tmp / "empty"
        empty.mkdir()
        res = self.json_cli("new", "--dry-run", "--worktree-root", "wt", cwd=empty)
        self.assertIn({"kind": "file", "target": ".gitignore", "detail": "ignore wt/"}, res["actions"])
        self.assertEqual(list(empty.iterdir()), [])

    def test_new_refuses_inside_existing_repo(self) -> None:
        outer = self.tmp / "outer"
        outer.mkdir()
        sh("git", "init", "-q", cwd=outer)
        p = self.run_cli("new", "inner", cwd=outer, expect=1)
        self.assertIn("inside another repository", p.stderr)
        self.assertFalse((outer / "inner").exists())
        (outer / "sub").mkdir()
        self.run_cli("new", str(outer / "sub"), cwd=self.tmp, expect=1)
        self.assertEqual(list((outer / "sub").iterdir()), [])

        # A repository root itself is fine; a second `new` there points at adopt.
        self.run_cli("new", cwd=outer)
        p = self.run_cli("new", cwd=outer, expect=1)
        self.assertIn("adopt", p.stderr)


class TestAdd(BaseFixture):
    def setUp(self) -> None:
        super().setUp()
        for name in ("app", "lib", "ref"):
            self.make_remote(name)
        self.root = self.tmp / "ws"
        self.run_cli("new", str(self.root), "--no-git-config", cwd=self.tmp)
        sh("git", "add", "-A", cwd=self.root)
        sh("git", "commit", "-qm", "scaffold", cwd=self.root)

    def url(self, name: str) -> str:
        return str(self.remotes[name][0])

    def test_add_submodule_stages_gitlink_and_policy(self) -> None:
        before = head_or_none(self.root)
        res = self.json_cli("add", self.url("app"), "--policy", "track", "--bump", "pr",
                            "--tier", "core", "--role", "Web client")
        self.assertEqual((res["name"], res["path"], res["kind"]), ("app", "app", "submodule"))
        _, seed = self.remotes["app"]
        self.assertEqual(res["gitlink"], sh("git", "rev-parse", "HEAD", cwd=seed))

        staged = set(sh("git", "diff", "--cached", "--name-only", cwd=self.root).splitlines())
        self.assertEqual(staged, {".gitmodules", "app"})
        self.assertEqual(head_or_none(self.root), before)  # never commits
        self.assertEqual(gm(self.root, "submodule.app.x-policy"), "track")
        self.assertEqual(gm(self.root, "submodule.app.x-bump"), "pr")
        self.assertEqual(gm(self.root, "submodule.app.x-tier"), "core")
        self.assertEqual(gm(self.root, "submodule.app.x-role"), "Web client")
        self.assertEqual(gm(self.root, "submodule.app.branch"), "main")  # from the child's origin/HEAD
        self.assertEqual(sh("git", "diff", "--name-only", "--", ".gitmodules", cwd=self.root), "")  # fully staged

        # --ref records a specific revision, and a custom name/path keep apart.
        old = sh("git", "rev-parse", "HEAD", cwd=self.remotes["lib"][1])
        self.upstream_commit("lib", "newer")
        res = self.json_cli("add", self.url("lib"), "libs/core-lib", "--name", "lib", "--ref", old)
        self.assertEqual((res["name"], res["path"], res["gitlink"]), ("lib", "libs/core-lib", old))
        self.assertEqual(gm(self.root, "submodule.lib.path"), "libs/core-lib")
        self.assertEqual(gm(self.root, "submodule.lib.x-policy"), "pin")

    def test_add_refuses_duplicate_and_nonempty_target(self) -> None:
        self.run_cli("add", self.url("app"))
        gitmodules = (self.root / ".gitmodules").read_text()
        self.run_cli("add", self.url("app"), expect=1)  # same path
        self.run_cli("add", self.url("lib"), "elsewhere", "--name", "app", expect=1)  # same name
        self.run_cli("add", self.url("lib"), "_tasks", expect=1)  # reserved

        (self.root / "occupied").mkdir()
        (self.root / "occupied" / "notes.txt").write_text("keep me")
        p = self.run_cli("add", self.url("lib"), "occupied", expect=1)
        self.assertIn("not empty", p.stderr)
        self.assertEqual((self.root / "occupied" / "notes.txt").read_text(), "keep me")
        self.assertEqual((self.root / ".gitmodules").read_text(), gitmodules)

        # Unstaged .gitmodules edits are someone's work in progress.
        sh("git", "config", "-f", ".gitmodules", "submodule.app.x-tier", "wip", cwd=self.root)
        p = self.run_cli("add", self.url("lib"), expect=1)
        self.assertIn("unstaged", p.stderr)
        self.assertFalse((self.root / "lib").exists())

        # A dry run describes the add and changes nothing.
        sh("git", "add", ".gitmodules", cwd=self.root)
        before = sh("git", "status", "--porcelain", cwd=self.root)
        res = self.json_cli("add", self.url("lib"), "--dry-run")
        self.assertTrue(any("submodule add" in a["target"] for a in res["actions"]))
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.root), before)
        self.assertFalse((self.root / "lib").exists())

    def test_add_lazy_sets_update_none(self) -> None:
        self.run_cli("add", self.url("ref"), "refs/ref", "--name", "ref", "--policy", "lazy", "--tier", "reference")
        self.assertEqual(gm(self.root, "submodule.ref.update"), "none")
        self.assertEqual(gm(self.root, "submodule.ref.x-policy"), "lazy")
        self.assertEqual(gm(self.root, "submodule.ref.branch"), "")  # lazy children follow no branch
        self.assertEqual(gm(self.root, "submodule.ref.x-bump"), "")
        self.run_cli("add", self.url("lib"), "--policy", "lazy", "--bump", "pr", expect=2)  # bump is track-only
        ref = self.json_cli("status")["submodules"][0]
        self.assertEqual((ref["name"], ref["policy"], ref["initialized"]), ("ref", "lazy", True))


class TestCheckoutState(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.adopt_policies()

    def test_init_preserves_drifted_checkout(self) -> None:
        local = self.commit(self.root / "app", "local work")
        res = self.json_cli("init", "app")["results"][0]
        self.assertEqual(res["action"], "skipped")
        self.assertTrue(res["drift"])
        self.assertEqual(res["head"], local)
        self.assertEqual(res["recorded"], self.gitlink("app"))
        self.assertEqual(sh("git", "rev-parse", "HEAD", cwd=self.root / "app"), local)
        self.assertIn("kept", self.run_cli("init", "app").stdout)

    def test_init_refuses_broken_checkout(self) -> None:
        store = self.root / ".git" / "modules" / "app"
        shutil.move(str(store), str(self.tmp / "app-store-elsewhere"))
        (self.root / "app" / "f.txt").write_text("unsaved edit\n")

        res = self.json_cli("init", "app", expect=1)["results"][0]
        self.assertEqual((res["action"], res["checkout"]), ("refused", "broken"))
        self.assertEqual((self.root / "app" / "f.txt").read_text(), "unsaved edit\n")
        self.assertFalse(store.exists())  # no `submodule update` recreated the store

        st = next(s for s in self.json_cli("status")["submodules"] if s["name"] == "app")
        self.assertEqual((st["initialized"], st["checkout"]), (False, "broken"))
        findings = self.json_cli("audit", expect=1)["findings"]
        self.assertIn(("checkout-broken", "error"), {(f["code"], f["level"]) for f in findings if f["subject"] == "app"})

        # Files without .git are refused the same way.
        (self.root / "lib" / ".git").unlink()
        res = self.json_cli("init", "lib", expect=1)["results"][0]
        self.assertEqual((res["action"], res["checkout"]), ("refused", "foreign"))

    def test_status_initialized_without_git_config_entry(self) -> None:
        sh("git", "config", "--remove-section", "submodule.app", cwd=self.root)
        st = next(s for s in self.json_cli("status")["submodules"] if s["name"] == "app")
        self.assertTrue(st["initialized"])
        self.assertEqual(st["checkout"], "ok")
        findings = {(f["code"], f["level"]) for f in self.json_cli("audit")["findings"] if f["subject"] == "app"}
        self.assertIn(("submodule-config-missing", "info"), findings)
        self.assertNotIn(("uninitialized", "warn"), findings)


if __name__ == "__main__":
    unittest.main()
