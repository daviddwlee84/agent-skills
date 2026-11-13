"""Orphan detection and `repair` against real severed worktree layouts.

Run: python3 -m unittest discover -s skills/local/superproject-workspace/tests -p 'test_repair.py' -v
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

from test_superproject import Fixture, sh


class RepairFixture(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.adopt_policies()

    def at_risk_worktree(self) -> tuple[Path, Path]:
        """A child worktree registered in the app store of a superproject linked worktree.

        Created with plain git: the CLI's guard refuses exactly this.
        """
        linked = self.linked_super("linked")
        wt = self.root / ".worktrees" / "app" / "feat"
        sh("git", "worktree", "add", "-q", "-b", "feat", str(wt), cwd=linked / "app")
        return linked, wt

    def findings(self, *args: str, expect: int = 0) -> dict[str, dict]:
        return {f["code"]: f for f in self.json_cli("audit", *args, expect=expect)["findings"]}

    def toplevel(self, d: Path) -> str | None:
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=d, capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else None


class TestRepair(RepairFixture):
    def test_audit_flags_superproject_worktree_and_at_risk(self) -> None:
        linked, wt = self.at_risk_worktree()
        f = self.findings()
        self.assertEqual(f["superproject-worktrees"]["level"], "warn")  # it has initialized modules
        self.assertEqual(f["worktree-at-risk"]["level"], "warn")
        self.assertIn(".worktrees/app/feat", f["worktree-at-risk"]["message"])
        self.assertNotIn("worktree-orphan", f)
        # repair never touches at-risk worktrees; it only lists them.
        before = sh("git", "worktree", "list", cwd=linked / "app")
        res = self.json_cli("repair", "--prune", "--reattach")
        self.assertEqual(res["actions"], [])
        self.assertEqual(sh("git", "worktree", "list", cwd=linked / "app"), before)
        # An outer worktree without submodules is only info; a non-default outer branch is info.
        self.sever(linked)
        shutil.rmtree(wt)
        sh("git", "worktree", "add", "-q", str(self.tmp / "docs-only"), cwd=self.root)
        sh("git", "switch", "-qc", "side", cwd=self.root)
        f = self.findings()
        self.assertEqual(f["superproject-worktrees"]["level"], "info")
        self.assertEqual(f["outer-branch"]["level"], "info")

    def test_repair_detects_orphan_after_superproject_worktree_removed(self) -> None:
        linked, wt = self.at_risk_worktree()
        self.sever(linked)
        self.assertIn("not a git repository", subprocess.run(
            ["git", "status"], cwd=wt, capture_output=True, text=True).stderr)
        f = self.findings(expect=1)
        self.assertEqual(f["worktree-orphan"]["level"], "error")
        self.assertIn("superproject-worktree-removed", f["worktree-orphan"]["message"])
        self.assertNotIn("superproject-worktrees", f)

        res = self.json_cli("repair", "--dry-run", expect=1)
        orphan = next(x for x in res["findings"] if x["code"] == "worktree-orphan")
        self.assertEqual((orphan["child"], orphan["cause"]), ("app", "superproject-worktree-removed"))
        self.assertEqual(Path(orphan["path"]).resolve(), wt.resolve())
        self.assertEqual(res["actions"], [])  # no flag: orphans are only listed
        self.assertTrue((wt / "f.txt").exists())

    def test_repair_reattach_preserves_files(self) -> None:
        linked, wt = self.at_risk_worktree()
        (wt / "f.txt").write_text("edited in the orphan\n")
        (wt / "new.txt").write_text("brand new\n")
        self.sever(linked)
        self.assertIsNone(self.toplevel(wt))

        dry = self.json_cli("repair", "--reattach", "--dry-run")
        self.assertEqual([a["kind"] for a in dry["actions"]], ["reattach"])
        self.assertIsNone(self.toplevel(wt))  # dry run changed nothing

        res = self.json_cli("repair", "--reattach")
        act = res["actions"][0]
        self.assertEqual((act["result"], act["branch"], act["base"]), ("done", "rescue/feat", self.gitlink("app")))
        self.assertEqual(res["remaining"], 0)

        self.assertEqual(Path(self.toplevel(wt)).resolve(), wt.resolve())
        self.assertEqual((wt / "f.txt").read_text(), "edited in the orphan\n")
        self.assertEqual((wt / "new.txt").read_text(), "brand new\n")
        self.assertEqual(sh("git", "branch", "--show-current", cwd=wt), "rescue/feat")
        # Unstaged modification against rescue/feat, nothing staged, new file untracked.
        self.assertEqual(sh("git", "diff", "--name-only", cwd=wt), "f.txt")
        self.assertEqual(sh("git", "diff", "--cached", "--name-only", cwd=wt), "")
        self.assertEqual(sh("git", "ls-files", "--others", "--exclude-standard", cwd=wt), "new.txt")
        # Now registered in the child's durable store, so the CLI manages it like any worktree.
        wts = [w for w in self.json_cli("worktree", "list")["worktrees"] if w["submodule"] == "app"]
        self.assertEqual([(w["branch"], w["dirty"], w["untracked"]) for w in wts], [("rescue/feat", 1, 1)])
        self.assertFalse((wt.parent / ".superproject-reattach").exists())
        f = self.findings()
        self.assertNotIn("worktree-orphan", f)
        self.assertNotIn("worktree-at-risk", f)
        sh("git", "add", "-A", cwd=wt)
        sh("git", "commit", "-qm", "rescued", cwd=wt)  # usable for normal work

    def test_repair_relinks_after_superproject_move(self) -> None:
        self.run_cli("worktree", "add", "app", "feat")
        moved = self.tmp / "moved"
        shutil.move(str(self.root), str(moved))
        self.root = moved
        wt = moved / ".worktrees" / "app" / "feat"
        self.assertIsNone(self.toplevel(wt))
        f = self.findings()
        self.assertEqual(f["worktree-relinkable"]["level"], "warn")

        res = self.json_cli("repair")
        self.assertEqual([(a["kind"], a["result"]) for a in res["actions"]], [("relink", "done")])
        self.assertEqual(Path(self.toplevel(wt)).resolve(), wt.resolve())
        self.assertNotIn("worktree-relinkable", self.findings())
        self.run_cli("worktree", "remove", "app", "feat", "--delete-branch")

    def test_repair_prune_only_with_flag(self) -> None:
        self.run_cli("worktree", "add", "app", "feat")
        shutil.rmtree(self.root / ".worktrees" / "app" / "feat")
        sh("git", "config", "submodule.gone.url", "https://example.com/gone.git", cwd=self.root)
        f = self.findings()
        self.assertEqual(f["worktree-prunable"]["level"], "info")
        self.assertEqual(f["stale-submodule-config"]["subject"], "gone")

        res = self.json_cli("repair")
        self.assertEqual(res["actions"], [])
        self.assertIn("prunable", sh("git", "worktree", "list", "--porcelain", cwd=self.root / "app"))

        self.json_cli("repair", "--prune", "--dry-run")
        self.assertIn("prunable", sh("git", "worktree", "list", "--porcelain", cwd=self.root / "app"))
        res = self.json_cli("repair", "--prune")
        self.assertEqual(sorted(a["kind"] for a in res["actions"]), ["prune", "remove-config"])
        self.assertEqual(res["remaining"], 0)
        self.assertNotIn("prunable", sh("git", "worktree", "list", "--porcelain", cwd=self.root / "app"))
        self.assertEqual(sh("git", "config", "--get", "submodule.gone.url", cwd=self.root, check=False), "")
        self.assertEqual(sh("git", "config", "--get", "submodule.app.url", cwd=self.root), str(self.remotes["app"][0]))

    def test_repair_delete_orphans_requires_explicit_path(self) -> None:
        self.run_cli("worktree", "add", "lib", "keep")
        orphan = self.root / ".worktrees" / "app" / "old"
        orphan.mkdir(parents=True)
        (orphan / ".git").write_text(f"gitdir: {self.tmp / 'vanished' / 'worktrees' / 'old'}\n")
        (orphan / "work.txt").write_text("last copy")
        f = self.findings(expect=1)
        self.assertIn("store-missing", f["worktree-orphan"]["message"])

        self.run_cli("repair", "--delete-orphans", expect=2)
        self.run_cli("repair", "--delete-orphans", ".worktrees/lib/keep", expect=1)  # healthy: refused
        self.assertTrue((self.root / ".worktrees" / "lib" / "keep" / "f.txt").exists())

        dry = self.json_cli("repair", "--delete-orphans", ".worktrees/app/old", "--dry-run")
        self.assertEqual((dry["actions"][0]["files"], dry["actions"][0]["result"]), (2, "planned"))
        self.assertTrue(dry["actions"][0]["latest_mtime"])
        self.assertTrue(orphan.exists())

        res = self.json_cli("repair", "--delete-orphans", ".worktrees/app/old")
        self.assertEqual(res["actions"][0]["result"], "done")
        self.assertFalse((self.root / ".worktrees" / "app").exists())
        self.assertTrue((self.root / ".worktrees" / "lib" / "keep").exists())

    def test_audit_reports_stale_config_and_store(self) -> None:
        sh("git", "rm", "-q", "lib", cwd=self.root)
        sh("git", "commit", "-qm", "drop lib", cwd=self.root)
        f = self.findings()
        self.assertEqual((f["stale-submodule-config"]["subject"], f["stale-submodule-config"]["level"]), ("lib", "info"))
        self.assertEqual((f["stale-module-store"]["subject"], f["stale-module-store"]["level"]), ("lib", "info"))
        store = self.root / ".git" / "modules" / "lib"

        self.json_cli("repair", "--prune")
        f = self.findings()
        self.assertNotIn("stale-submodule-config", f)
        self.assertIn("stale-module-store", f)  # stores are never deleted automatically
        self.assertTrue((store / "HEAD").exists())


if __name__ == "__main__":
    unittest.main()
