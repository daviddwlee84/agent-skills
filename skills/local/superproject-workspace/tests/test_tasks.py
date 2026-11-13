"""Worktree root, durable-store guard, and cross-child task worktrees.

Run: python3 -m unittest discover -s skills/local/superproject-workspace/tests -p 'test_tasks.py' -v
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from test_superproject import Fixture, sh


class TasksFixture(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.adopt_policies()
        self.tasks = self.root / ".worktrees" / "_tasks"

    def branches(self, child: str) -> list[str]:
        return sh("git", "branch", "--format=%(refname:short)", cwd=self.root / child).splitlines()


class TestWorktreeRoot(TasksFixture):
    def test_worktree_root_from_tracked_config(self) -> None:
        sh("git", "config", "-f", ".superproject", "workspace.worktree-root", "wt", cwd=self.root)
        res = self.json_cli("worktree", "add", "app", "feat/x")
        self.assertEqual(res["path"], "wt/app/feat-x")
        self.assertTrue(res["gitignore_updated"])
        self.assertIn("wt/", (self.root / ".gitignore").read_text())
        self.assertEqual(sh("git", "status", "--porcelain", "--", "wt", cwd=self.root), "")
        items = self.json_cli("worktree", "list")["worktrees"]
        self.assertEqual([(w["path"], w["managed"]) for w in items], [("wt/app/feat-x", True)])

    def test_worktree_root_local_override(self) -> None:
        ext = (self.tmp / "elsewhere").resolve()
        sh("git", "config", "--local", "superproject.worktreeRoot", str(ext), cwd=self.root)
        gitignore = (self.root / ".gitignore").read_text()
        res = self.json_cli("worktree", "add", "app", "feat")
        self.assertEqual(res["path"], str(ext / "app" / "feat"))
        self.assertFalse(res["gitignore_updated"])
        self.assertEqual((self.root / ".gitignore").read_text(), gitignore)

        # The root is found again from inside the outside worktree (store common dir).
        st = self.json_cli("status", cwd=ext / "app" / "feat")
        self.assertEqual(Path(st["root"]).resolve(), self.root.resolve())
        codes = {f["code"]: f["level"] for f in self.json_cli("audit")["findings"]}
        self.assertEqual(codes.get("worktree-outside-root"), "info")
        self.assertNotIn("worktrees-not-ignored", codes)

        # Worktrees elsewhere show only with --all.
        sh("git", "worktree", "add", "-q", "-b", "side", str(self.tmp / "adhoc"), cwd=self.root / "app")
        managed = [w["path"] for w in self.json_cli("worktree", "list")["worktrees"]]
        everything = {w["path"]: w["managed"] for w in self.json_cli("worktree", "list", "--all")["worktrees"]}
        self.assertEqual(managed, [str(ext / "app" / "feat")])
        self.assertEqual(everything[str((self.tmp / "adhoc").resolve())], False)

    def test_worktree_add_refused_in_linked_superproject(self) -> None:
        linked = self.linked_super("linked")
        p = self.run_cli("worktree", "add", "app", "feat", cwd=linked, expect=1)
        self.assertIn(str(self.root.resolve()), p.stderr)  # names the main checkout
        self.assertFalse((linked / ".worktrees").exists())
        self.run_cli("task", "open", "demo", "app", cwd=linked, expect=1)
        self.run_cli("add", str(self.remotes["app"][0]), "app2", cwd=linked, expect=1)
        self.assertFalse((linked / "app2").exists())
        # The main checkout is unaffected.
        self.run_cli("worktree", "add", "app", "feat")


class TestTasks(TasksFixture):
    def test_task_open_creates_members_same_branch(self) -> None:
        self.upstream_commit("lib", "upstream moved")
        res = self.json_cli("task", "open", "demo", "app", "lib")
        members = {m["child"]: m for m in res["members"]}
        self.assertEqual(res["path"], ".worktrees/_tasks/demo")
        self.assertEqual({m["action"] for m in members.values()}, {"created"})
        self.assertEqual(members["app"]["base"], "origin/main")
        self.assertEqual(members["lib"]["base"], self.gitlink("lib"))  # pins start at the baseline
        for child in ("app", "lib"):
            wt = self.tasks / "demo" / child
            self.assertTrue((wt / "f.txt").exists())
            self.assertEqual(sh("git", "branch", "--show-current", cwd=wt), "demo")
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.root), "")
        tasks = {w["submodule"]: w["task"] for w in self.json_cli("worktree", "list")["worktrees"]}
        self.assertEqual(tasks, {"app": "demo", "lib": "demo"})
        self.assertIn("TASK", self.run_cli("worktree", "list").stdout)

    def test_task_open_is_idempotent_and_extends(self) -> None:
        self.run_cli("task", "open", "demo", "app")
        res = self.json_cli("task", "open", "demo", "app", "lib")
        self.assertEqual({m["child"]: m["action"] for m in res["members"]}, {"app": "exists", "lib": "created"})
        self.assertEqual(self.branches("app").count("demo"), 1)
        # A different branch for an existing member is refused, and nothing else is created.
        p = self.run_cli("task", "open", "demo", "app", "ref", "--branch", "other", expect=1)
        self.assertIn("changed nothing", p.stderr)
        self.assertFalse((self.tasks / "demo" / "ref").exists())
        self.run_cli("task", "open", "bad..name", "app", expect=2)

    def test_task_open_rolls_back_on_failure(self) -> None:
        # A failing post-checkout hook makes `git worktree add` exit 1 after creating the worktree.
        hook = self.root / ".git" / "modules" / "lib" / "hooks" / "post-checkout"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        res = self.json_cli("task", "open", "demo", "app", "lib", expect=1)
        self.assertEqual({m["child"]: m["action"] for m in res["members"]}, {"app": "rolled-back", "lib": "failed"})
        self.assertFalse((self.root / ".worktrees" / "_tasks").exists())
        self.assertNotIn("demo", self.branches("app"))
        self.assertNotIn("demo", self.branches("lib"))
        self.assertEqual(len(sh("git", "worktree", "list", cwd=self.root / "lib").splitlines()), 1)
        hook.unlink()
        self.run_cli("task", "open", "demo", "app", "lib")  # clean retry

    def test_task_list_reports_dirty_and_merged(self) -> None:
        self.run_cli("task", "open", "demo", "app", "lib")
        app, lib = self.tasks / "demo" / "app", self.tasks / "demo" / "lib"
        (app / "f.txt").write_text("edited\n")
        (app / "scratch.txt").write_text("x")
        self.commit(lib, "lib change")
        (self.tasks / "demo" / "notes.md").write_text("stray")

        t = self.json_cli("task", "list", "demo")["tasks"][0]
        m = {x["child"]: x for x in t["members"]}
        self.assertEqual((m["app"]["dirty"], m["app"]["untracked"]), (1, 1))
        self.assertEqual((m["lib"]["dirty"], m["lib"]["unpushed"], m["lib"]["merged"]), (0, 1, False))
        self.assertEqual(t["stray_dirs"], [".worktrees/_tasks/demo/notes.md"])
        self.assertFalse(t["ready_to_close"])

        sh("git", "checkout", "-q", "--", "f.txt", cwd=app)
        os.remove(app / "scratch.txt")
        os.remove(self.tasks / "demo" / "notes.md")
        sh("git", "push", "-q", "origin", "HEAD:main", cwd=lib)  # "merged" upstream
        sh("git", "fetch", "-q", "origin", cwd=self.root / "lib")
        sh("git", "fetch", "-q", "origin", cwd=self.root / "app")
        t = self.json_cli("task", "list")["tasks"][0]
        m = {x["child"]: x for x in t["members"]}
        self.assertTrue(m["lib"]["merged"])
        self.assertEqual(m["lib"]["unpushed"], 0)
        self.assertTrue(t["ready_to_close"])

    def test_task_close_atomic_refusal_then_force(self) -> None:
        self.run_cli("task", "open", "demo", "app", "lib")
        app, lib = self.tasks / "demo" / "app", self.tasks / "demo" / "lib"
        (app / "untracked.txt").write_text("keep?")
        p = self.run_cli("task", "close", "demo", expect=1)
        self.assertIn("app: 0 modified, 1 untracked", p.stderr)
        self.assertTrue(app.exists() and lib.exists())  # all-or-nothing

        os.remove(app / "untracked.txt")
        self.commit(lib, "unmerged work")
        p = self.run_cli("task", "close", "demo", "--delete-branch", expect=1)
        self.assertIn("lib: branch demo is not merged", p.stderr)
        self.assertTrue(app.exists() and lib.exists())
        self.assertIn("demo", self.branches("lib"))

        dry = self.json_cli("task", "close", "demo", "--delete-branch", "--force", "--dry-run")
        self.assertEqual({m["action"] for m in dry["members"]}, {"would-close"})
        self.assertTrue(lib.exists())

        self.run_cli("task", "close", "demo", "--delete-branch", "--force")
        self.assertFalse((self.root / ".worktrees" / "_tasks").exists())  # empty parents removed
        self.assertTrue((self.root / ".worktrees").exists())  # the root itself stays
        self.assertNotIn("demo", self.branches("app"))
        self.assertNotIn("demo", self.branches("lib"))
        self.assertEqual(self.json_cli("task", "list")["tasks"], [])


if __name__ == "__main__":
    unittest.main()
