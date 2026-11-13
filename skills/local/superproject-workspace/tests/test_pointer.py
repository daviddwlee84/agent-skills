"""Pointer-only home repo: `.superproject` [repo] children, clone on demand, repo map.

Run: python3 -m unittest discover -s skills/local/superproject-workspace/tests -p 'test_pointer.py' -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

from test_superproject import BaseFixture, sh


def marker(root: Path, key: str) -> str:
    return sh("git", "config", "-f", ".superproject", "--get", key, cwd=root, check=False)


class PointerFixture(BaseFixture):
    def setUp(self) -> None:
        super().setUp()
        for name in ("docs", "infra", "app"):
            self.make_remote(name)
        self.root = self.tmp / "home"
        self.run_cli("new", str(self.root), "--mode", "pointer", cwd=self.tmp)

    def url(self, name: str) -> str:
        return str(self.remotes[name][0])

    def state(self, name: str) -> dict:
        return next(s for s in self.json_cli("status")["submodules"] if s["name"] == name)

    def codes(self, expect: int = 0) -> dict[str, dict]:
        return {f["code"]: f for f in self.json_cli("audit", expect=expect)["findings"]}


class TestPointer(PointerFixture):
    def test_pointer_add_clone_status(self) -> None:
        self.assertIn("home repo", (self.root / "AGENTS.md").read_text())  # pointer template
        self.assertEqual(sh("git", "config", "--local", "--get", "diff.submodule", cwd=self.root, check=False), "")
        res = self.json_cli("add", self.url("docs"), "--role", "Public docs site", "--tier", "reference")
        self.assertEqual((res["kind"], res["name"], res["path"], res["branch"]), ("pointer", "docs", "repos/docs", "main"))
        self.assertTrue((self.root / "repos" / "docs" / "f.txt").exists())
        self.assertEqual(marker(self.root, "repo.docs.url"), self.url("docs"))
        self.assertEqual(marker(self.root, "repo.docs.x-role"), "Public docs site")
        self.assertIn("/repos/docs/", (self.root / ".gitignore").read_text())
        self.assertEqual(sh("git", "diff", "--cached", "--name-only", cwd=self.root), "")  # nothing staged
        self.assertEqual(sh("git", "status", "--porcelain", "--", "repos", cwd=self.root), "")

        self.upstream_commit("docs", "newer docs")
        st = next(s for s in self.json_cli("status", "--fetch")["submodules"] if s["name"] == "docs")
        self.assertEqual((st["kind"], st["policy"], st["recorded"], st["lag"]), ("pointer", "pointer", None, 1))
        row = next(line for line in self.run_cli("status").stdout.splitlines() if line.startswith("docs"))
        self.assertEqual(row.split()[2:6], ["pointer", "manual", "reference", "-"])

        self.assertEqual({k: v["level"] for k, v in self.codes().items()
                          if k.startswith("pointer") or k == "push-check"}, {})
        # A clone whose origin moved, a lost ignore rule, and a committed clone are all flagged.
        sh("git", "remote", "set-url", "origin", "https://example.com/elsewhere.git", cwd=self.root / "repos" / "docs")
        (self.root / ".gitignore").write_text(".worktrees/\n")
        codes = self.codes()
        self.assertEqual(codes["pointer-url-mismatch"]["level"], "warn")
        self.assertEqual(codes["pointer-not-ignored"]["level"], "warn")
        self.json_cli("add", self.url("infra"), "repos/infra-copy", "--name", "infra", "--no-clone")
        (self.root / "repos" / "infra-copy").mkdir()
        (self.root / "repos" / "infra-copy" / "x.txt").write_text("x")
        sh("git", "add", "-f", "repos/infra-copy/x.txt", cwd=self.root)  # forced past the ignore rule
        self.assertEqual(self.codes(expect=1)["pointer-tracked"]["level"], "error")

    def test_pointer_init_on_demand_only(self) -> None:
        self.run_cli("add", self.url("docs"), "--no-clone", "--tier", "reference")
        self.run_cli("add", self.url("infra"), "--no-clone")
        self.assertFalse((self.root / "repos").exists())
        self.assertEqual(self.state("docs")["checkout"], "absent")
        self.assertIn("clone on demand", self.run_cli("status").stdout)

        self.assertEqual(self.json_cli("init")["results"], [])  # pointers are never cloned implicitly
        self.assertFalse((self.root / "repos").exists())
        res = self.json_cli("init", "--tier", "reference")["results"]
        self.assertEqual([(r["name"], r["action"]) for r in res], [("docs", "initialized")])
        self.assertTrue((self.root / "repos" / "docs" / ".git").is_dir())
        self.assertFalse((self.root / "repos" / "infra").exists())
        self.assertEqual(self.json_cli("init", "infra", "--dry-run")["results"][0]["action"], "would-init")
        self.assertFalse((self.root / "repos" / "infra").exists())
        self.json_cli("init", "infra")
        self.assertEqual(self.state("infra")["checkout"], "ok")
        self.assertEqual(self.json_cli("init", "--kind", "pointer")["results"][0]["action"], "skipped")

        # Files where a clone should go are never overwritten.
        self.run_cli("add", self.url("app"), "--no-clone")
        (self.root / "repos" / "app").mkdir()
        (self.root / "repos" / "app" / "draft.txt").write_text("mine")
        res = self.json_cli("init", "app", expect=1)["results"][0]
        self.assertEqual((res["action"], res["checkout"]), ("refused", "foreign"))
        self.assertEqual((self.root / "repos" / "app" / "draft.txt").read_text(), "mine")

    def test_pointer_outside_root_and_worktree(self) -> None:
        outside = self.tmp / "clones" / "infra"
        gitignore = (self.root / ".gitignore").read_text()
        res = self.json_cli("add", self.url("infra"), "../clones/infra")
        self.assertEqual(res["path"], "../clones/infra")
        self.assertTrue((outside / "f.txt").exists())
        self.assertEqual((self.root / ".gitignore").read_text(), gitignore)  # outside: nothing to ignore
        self.assertNotIn("pointer-path-absolute", self.codes())
        self.run_cli("add", self.url("docs"), str(self.tmp / "abs-docs"))
        self.assertEqual(self.codes()["pointer-path-absolute"]["level"], "info")

        # An existing clone with the same origin is adopted in place; another origin is refused.
        sh("git", "clone", "-q", self.url("app"), str(self.tmp / "clones" / "app"), cwd=self.tmp)
        res = self.json_cli("add", self.url("app"), "../clones/app")
        self.assertIn("adopt", [a["kind"] for a in res["actions"]])
        self.run_cli("add", self.url("docs"), "../clones/app", "--name", "other", expect=1)

        res = self.json_cli("worktree", "add", "infra", "feat")
        self.assertEqual((res["path"], res["base"]), (".worktrees/infra/feat", "origin/main"))
        st = self.json_cli("status", cwd=self.root / ".worktrees" / "infra" / "feat")
        self.assertEqual(Path(st["root"]).resolve(), self.root.resolve())
        res = self.json_cli("task", "open", "demo", "infra", "app")
        self.assertEqual({m["child"] for m in res["members"]}, {"infra", "app"})
        self.assertTrue((self.root / ".worktrees" / "_tasks" / "demo" / "infra" / "f.txt").exists())
        self.commit(self.root / ".worktrees" / "_tasks" / "demo" / "app", "change")
        members = {m["child"]: m for m in self.json_cli("task", "list", "demo")["tasks"][0]["members"]}
        self.assertEqual((members["app"]["kind"], members["app"]["unpushed"]), ("pointer", 1))
        self.run_cli("task", "close", "demo", "--delete-branch", "--force")
        self.run_cli("worktree", "remove", "infra", "feat", "--delete-branch")
        self.assertNotIn("worktree-orphan", self.codes())

    def test_pointer_bump_refused(self) -> None:
        self.run_cli("add", self.url("docs"))
        res = self.json_cli("bump", "docs", "--reason", "x", expect=1)
        self.assertEqual(res["results"][0]["action"], "refused")
        self.assertIn("no gitlink", res["results"][0]["reason"])
        p = self.run_cli("ci-plan", "--only", "docs", expect=1)
        self.assertIn("submodule", p.stderr)
        self.assertEqual(self.json_cli("ci-plan")["init_paths"], [])
        self.assertEqual(self.json_cli("pull")["results"], [])  # only when named

        new = self.upstream_commit("docs", "newer")
        res = self.json_cli("pull", "docs")["results"][0]  # named: ff-only, no --force needed
        self.assertEqual((res["action"], res["to"]), ("updated", new))
        self.assertEqual(sh("git", "rev-parse", "HEAD", cwd=self.root / "repos" / "docs"), new)


class TestRepoMap(PointerFixture):
    def test_repo_map_rendered_and_stale_detected(self) -> None:
        agents = self.root / "AGENTS.md"
        self.assertIn("No repositories yet", agents.read_text())
        self.run_cli("add", self.url("docs"), "--role", "Public docs site", "--tier", "reference")
        self.run_cli("add", self.url("app"), "--submodule", "--policy", "track", "--role", "Web client | API")
        text = agents.read_text()
        self.assertIn("| docs | Public docs site | `repos/docs` | pointer | reference | `init docs` |", text)
        self.assertIn("| app | Web client \\| API | `app` | submodule (track) | - | `init app` |", text)
        self.assertNotIn("repo-map-stale", self.codes())

        sh("git", "config", "-f", ".superproject", "repo.docs.x-role", "Docs and blog", cwd=self.root)
        self.assertEqual(self.codes()["repo-map-stale"]["level"], "warn")
        # A submodule child now exists, so adopt switches to the submodule template too.
        actions = {a["detail"] for a in self.json_cli("adopt", "--no-git-config")["actions"]}
        self.assertIn("upsert repo map", actions)
        self.assertIn("Docs and blog", agents.read_text())
        self.assertIn("Working across submodules", agents.read_text())
        codes = self.codes()
        self.assertNotIn("repo-map-stale", codes)
        self.assertNotIn("managed-block-stale", codes)
        self.assertEqual(self.json_cli("adopt", "--no-git-config")["actions"], [])  # idempotent

    def test_map_file_progressive_disclosure(self) -> None:
        for i in range(26):
            tier = "reference" if i % 2 else "core"
            self.run_cli("add", f"https://example.com/org/r{i:02}.git", "--no-clone", "--tier", tier)
        agents = self.root / "AGENTS.md"
        self.assertEqual(agents.read_text().count("| `init r"), 26)
        self.assertEqual(self.codes()["repo-map-large"]["level"], "info")

        sh("git", "config", "-f", ".superproject", "workspace.map-file", "docs/repos.md", cwd=self.root)
        self.assertEqual(self.codes()["repo-map-stale"]["level"], "warn")
        self.run_cli("adopt", "--no-git-config")
        full = (self.root / "docs" / "repos.md").read_text()
        self.assertIn("## core", full)
        self.assertIn("## reference", full)
        self.assertEqual(full.count("| `init r"), 26)
        short = agents.read_text()
        self.assertIn("26 repositories (core: 13, reference: 13)", short)
        self.assertIn("[`docs/repos.md`](docs/repos.md)", short)
        self.assertNotIn("`init r00`", short)
        codes = self.codes()
        self.assertNotIn("repo-map-large", codes)
        self.assertNotIn("repo-map-stale", codes)


if __name__ == "__main__":
    unittest.main()
