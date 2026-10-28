"""End-to-end tests for scripts/superproject.py against throwaway local repos.

Run: python3 -m unittest discover -s skills/local/superproject-workspace/tests -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "scripts" / "superproject.py"


def sh(*args: str, cwd: Path, check: bool = True) -> str:
    p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise AssertionError(f"{' '.join(args)} failed: {p.stderr}")
    return p.stdout.strip()


class Fixture(unittest.TestCase):
    """Superproject with children `app` (track/pr), `lib` (pin), `ref` (lazy)."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="superproject-test-"))
        gitconfig = self.tmp / "gitconfig"
        gitconfig.write_text(
            "[user]\n\tname = Test\n\temail = test@example.com\n"
            "[init]\n\tdefaultBranch = main\n"
            "[protocol \"file\"]\n\tallow = always\n"
            "[commit]\n\tgpgsign = false\n"
        )
        self._env = {k: os.environ.get(k) for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")}
        os.environ["GIT_CONFIG_GLOBAL"] = str(gitconfig)
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"

        self.remotes = {}
        for name in ("app", "lib", "ref"):
            bare = self.tmp / "remotes" / f"{name}.git"
            sh("git", "init", "--bare", "-q", str(bare), cwd=self.tmp)
            seed = self.tmp / "seed" / name
            sh("git", "clone", "-q", str(bare), str(seed), cwd=self.tmp)
            self.commit(seed, "init")
            sh("git", "push", "-q", "origin", "main", cwd=seed)
            self.remotes[name] = (bare, seed)

        self.root = self.tmp / "super"
        self.root.mkdir()
        sh("git", "init", "-q", cwd=self.root)
        for name, (bare, _) in self.remotes.items():
            sh("git", "submodule", "add", "-q", str(bare), name, cwd=self.root)
        sh("git", "commit", "-qm", "add children", cwd=self.root)

    def tearDown(self) -> None:
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        subprocess.run(["rm", "-rf", str(self.tmp)])

    # helpers
    def commit(self, repo: Path, msg: str) -> str:
        (repo / "f.txt").write_text((repo / "f.txt").read_text() + msg + "\n" if (repo / "f.txt").exists() else msg + "\n")
        sh("git", "add", "f.txt", cwd=repo)
        sh("git", "commit", "-qm", msg, cwd=repo)
        return sh("git", "rev-parse", "HEAD", cwd=repo)

    def upstream_commit(self, name: str, msg: str) -> str:
        _, seed = self.remotes[name]
        sha = self.commit(seed, msg)
        sh("git", "push", "-q", "origin", "main", cwd=seed)
        return sha

    def run_cli(self, *args: str, expect: int = 0, cwd: Path | None = None) -> subprocess.CompletedProcess:
        p = subprocess.run([sys.executable, str(CLI), *args], cwd=cwd or self.root, capture_output=True, text=True)
        self.assertEqual(p.returncode, expect, f"{args}: rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}")
        return p

    def json_cli(self, *args: str, expect: int = 0) -> dict:
        return json.loads(self.run_cli(*args, "--json", expect=expect).stdout)

    def adopt_policies(self) -> None:
        self.run_cli("adopt", "--set", "app=track:pr", "--set", "lib=pin", "--set", "ref=lazy",
                     "--no-git-config")
        sh("git", "add", "-A", cwd=self.root)
        sh("git", "commit", "-qm", "adopt", cwd=self.root)

    def gitlink(self, path: str) -> str:
        return sh("git", "ls-tree", "HEAD", "--", path, cwd=self.root).split()[2]


class TestAuditAdopt(Fixture):
    def test_audit_flags_missing_policy_then_adopt_fixes_it(self) -> None:
        codes = {f["code"] for f in self.json_cli("audit")["findings"]}
        self.assertIn("policy-missing", codes)
        self.assertIn("agents-block", codes)

        self.adopt_policies()
        findings = self.json_cli("audit")["findings"]
        codes = {f["code"] for f in findings}
        self.assertNotIn("policy-missing", codes)
        self.assertNotIn("agents-block", codes)
        self.assertNotIn("worktrees-not-ignored", codes)
        self.assertIn("ci-missing", codes)  # app wants pr bumps, no workflow yet

        gm = sh("git", "config", "-f", ".gitmodules", "--get", "submodule.ref.update", cwd=self.root)
        self.assertEqual(gm, "none")
        self.assertTrue((self.root / "scripts" / "superproject.py").exists())

    def test_adopt_is_idempotent(self) -> None:
        self.adopt_policies()
        actions = self.json_cli("adopt", "--no-git-config")["actions"]
        self.assertEqual(actions, [])
        agents = (self.root / "AGENTS.md").read_text()
        self.assertEqual(agents.count("superproject-workspace:agent-guidance -->"), 2)  # begin + end
        self.assertEqual(agents.count("(end)"), 1)

    def test_adopt_dry_run_writes_nothing(self) -> None:
        before = sh("git", "status", "--porcelain", cwd=self.root)
        actions = self.json_cli("adopt", "--dry-run", "--with-ci")["actions"]
        self.assertTrue(actions)
        self.assertEqual(sh("git", "status", "--porcelain", cwd=self.root), before)

    def test_ci_plan_groups_by_mode(self) -> None:
        self.adopt_policies()
        plan = self.json_cli("ci-plan")
        self.assertEqual([x["name"] for x in plan["pr"]], ["app"])
        self.assertEqual(plan["direct"], [])


class TestPullBump(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.adopt_policies()

    def test_lag_pull_bump_commit(self) -> None:
        new = self.upstream_commit("app", "upstream change")
        app = next(s for s in self.json_cli("status", "--fetch")["submodules"] if s["name"] == "app")
        self.assertEqual(app["lag"], 1)

        self.run_cli("pull", "app")
        self.assertEqual(sh("git", "rev-parse", "HEAD", cwd=self.root / "app"), new)
        self.assertNotEqual(self.gitlink("app"), new)  # pull never touches the gitlink

        res = self.json_cli("bump", "--all-track", "--commit")
        self.assertTrue(res["commit"])
        self.assertEqual(self.gitlink("app"), new)
        msg = sh("git", "log", "-1", "--format=%B", cwd=self.root)
        self.assertIn("chore(submodules): bump app", msg)
        self.assertIn("upstream change", msg)  # --submodule=log summary

    def test_pull_refuses_pin_without_force(self) -> None:
        self.upstream_commit("lib", "newer")
        res = self.json_cli("pull", "lib", expect=1)
        self.assertEqual(res["results"][0]["action"], "refused")
        self.run_cli("pull", "lib", "--force")

    def test_pull_refuses_feature_branch_checkout(self) -> None:
        sh("git", "switch", "-qc", "feat", cwd=self.root / "app")
        res = self.json_cli("pull", "app", expect=1)
        self.assertIn("worktree", res["results"][0]["reason"])

    def test_bump_refuses_unpushed_commit(self) -> None:
        self.commit(self.root / "app", "local only")
        res = self.json_cli("bump", "app", "--commit", expect=1)
        self.assertEqual(res["results"][0]["action"], "refused")
        self.assertIn("not reachable", res["results"][0]["reason"])
        self.assertIsNone(res["commit"])

    def test_bump_pin_requires_reason(self) -> None:
        self.upstream_commit("lib", "newer")
        self.run_cli("pull", "lib", "--force")
        self.json_cli("bump", "lib", expect=1)
        res = self.json_cli("bump", "lib", "--reason", "deploy baseline v2", "--commit")
        self.assertTrue(res["commit"])
        self.assertIn("Reason: deploy baseline v2", sh("git", "log", "-1", "--format=%B", cwd=self.root))

    def test_pin_may_point_at_another_pushed_branch(self) -> None:
        lib = self.root / "lib"
        sh("git", "switch", "-qc", "release", cwd=lib)
        self.commit(lib, "release-only fix")
        sh("git", "push", "-q", "origin", "release", cwd=lib)
        self.json_cli("bump", "lib", "--reason", "prod baseline", "--commit")
        codes = {f["code"]: f["level"] for f in self.json_cli("audit")["findings"] if f["subject"] == "lib"}
        self.assertNotIn("gitlink-unreachable", codes)
        self.assertEqual(codes.get("gitlink-off-branch"), "info")

    def test_bump_is_atomic_unless_partial(self) -> None:
        self.upstream_commit("app", "good")
        self.run_cli("pull", "app")
        self.commit(self.root / "lib", "unpushed")
        res = self.json_cli("bump", "app", "lib", "--reason", "x", "--commit", expect=1)
        actions = {r["name"]: r["action"] for r in res["results"]}
        self.assertEqual(actions, {"app": "aborted", "lib": "refused"})
        self.assertEqual(sh("git", "diff", "--cached", "--name-only", cwd=self.root), "")

    def test_bump_refuses_other_staged_changes(self) -> None:
        self.upstream_commit("app", "good")
        self.run_cli("pull", "app")
        (self.root / "notes.txt").write_text("x")
        sh("git", "add", "notes.txt", cwd=self.root)
        p = self.run_cli("bump", "app", "--commit", expect=1)
        self.assertIn("notes.txt", p.stderr)


class TestPreflight(Fixture):
    def test_preflight_catches_unpushed_staged_gitlink(self) -> None:
        self.assertIn("No staged gitlink", self.run_cli("preflight").stdout)
        self.commit(self.root / "app", "local only")
        sh("git", "add", "app", cwd=self.root)
        res = self.json_cli("preflight", expect=1)
        self.assertFalse(res["ok"])
        sh("git", "push", "-q", "origin", "HEAD:main", cwd=self.root / "app")
        sh("git", "fetch", "-q", "origin", cwd=self.root / "app")
        self.assertTrue(self.json_cli("preflight")["ok"])


class TestInitWorktree(Fixture):
    def setUp(self) -> None:
        super().setUp()
        self.adopt_policies()
        sh("git", "submodule", "--quiet", "deinit", "-f", "ref", cwd=self.root)

    def test_init_skips_lazy_unless_named(self) -> None:
        res = self.json_cli("init")
        self.assertNotIn("ref", [r["name"] for r in res["results"]])
        self.assertFalse((self.root / "ref" / ".git").exists())
        res = self.json_cli("init", "ref")
        self.assertEqual(res["results"][0]["action"], "initialized")
        self.assertTrue((self.root / "ref" / ".git").exists())

    def test_worktree_add_list_remove(self) -> None:
        res = self.json_cli("worktree", "add", "app", "feat/x")
        self.assertEqual(res["path"], ".worktrees/app/feat-x")
        self.assertTrue((self.root / ".worktrees" / "app" / "feat-x" / "f.txt").exists())
        self.assertEqual(sh("git", "status", "--porcelain", "--", ".worktrees", cwd=self.root), "")

        items = self.json_cli("worktree", "list")["worktrees"]
        self.assertEqual([(w["submodule"], w["branch"]) for w in items], [("app", "feat/x")])

        self.run_cli("worktree", "remove", "app", "feat/x", "--delete-branch")
        self.assertFalse((self.root / ".worktrees" / "app" / "feat-x").exists())
        self.assertEqual(sh("git", "branch", "--list", "feat/x", cwd=self.root / "app"), "")

    def test_pinned_worktree_branches_from_gitlink(self) -> None:
        self.upstream_commit("lib", "upstream moved")
        res = self.json_cli("worktree", "add", "lib", "fix")
        self.assertEqual(res["base"], self.gitlink("lib"))

    def test_cli_finds_root_from_child_worktree(self) -> None:
        self.run_cli("worktree", "add", "app", "feat")
        p = self.run_cli("status", "--json", cwd=self.root / ".worktrees" / "app" / "feat")
        self.assertEqual(Path(json.loads(p.stdout)["root"]).resolve(), self.root.resolve())


if __name__ == "__main__":
    unittest.main()
