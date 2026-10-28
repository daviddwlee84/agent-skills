# Automated bumps in CI

`adopt --with-ci` installs `.github/workflows/superproject-bump.yml`:

1. `ci-plan --json` lists `track` children with `x-bump` `pr` or `direct`.
   Use `--only` to select one child, as `workflow_dispatch` and
   `repository_dispatch` do.
2. `init` checks out just those children.
3. **direct:** `pull` → `bump --commit` → push to the default branch.
4. **pr:** switch to the fixed branch `chore/submodule-bump` → `pull` →
   `bump --commit` → force-push → open the PR once (later runs update it).

The job fails, with a red run, when `pull` or `bump` refuses. Typical causes:
a child's history was rewritten (diverged), or the gitlink points at a
deleted commit. Fix those by hand.

## Credentials

| Children | Secret | Notes |
|---|---|---|
| Public | none | `GITHUB_TOKEN` can push the outer repo |
| Private on GitHub | `SUBMODULE_TOKEN` | Fine-grained PAT (or GitHub App token) with *Contents: read* on each child. The workflow rewrites `git@github.com:` and `https://github.com/` to use it. |
| GitLab | `GITLAB_TOKEN` | Project or group access token with `read_repository`; rewritten the same way |
| Other forges | add another `insteadOf` line | |

SSH URLs in `.gitmodules` are fine for humans. The `insteadOf` rewrite maps
them to HTTPS in CI.

## Gotchas

- **PRs created with `GITHUB_TOKEN` do not trigger `pull_request` workflows.**
  Either run validation in the bump job itself, or create the PR with a PAT or
  App token.
- **`direct` with branch protection** needs a token that may bypass it, or
  else use `pr`.
- **Schedule vs dispatch:** a schedule is simple and needs no child changes.
  For near-immediate bumps, add `assets/child-dispatch.yml` to each child.
  This needs a PAT with *Contents: write* on the superproject, because
  `repository_dispatch` requires it.
- **GitLab-hosted superprojects:** port the same steps to `.gitlab-ci.yml`
  with a scheduled pipeline and `glab mr create`. The CLI is forge-agnostic.
