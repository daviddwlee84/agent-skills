# Forge Abstraction: gh vs glab

The `forge.sh` library provides a unified interface over two forge CLIs.
This reference documents the mapping, gaps, and escape hatches.

## Detection

`forge_detect` parses `git remote get-url origin`:

| URL pattern | Detected as | CLI used |
|---|---|---|
| `*github.com*` | `github` | `gh` |
| `*gitlab.com*` or `*gitlab.*` | `gitlab` | `glab` |
| anything else | `unknown` | (error) |

Self-hosted GitLab instances are detected by the `gitlab.` pattern in the
URL (e.g., `gitlab.mycompany.com`). Self-hosted GitHub Enterprise is also
matched by the `github.com` pattern if the remote uses that domain.

## Command mapping

### Issues

| Operation | `forge.sh` function | `gh` command | `glab` command |
|---|---|---|---|
| Create | `forge_issue_create` | `gh issue create --title --body --label --assignee` | `glab issue create --title --description --label --assignee --no-editor` |
| List | `forge_issue_list` | `gh issue list --state --label --assignee --limit --json` | `glab issue list --opened/--closed --label --assignee --per-page --output json` |
| View | `forge_issue_view` | `gh issue view N --json` | `glab issue view N --output json` |
| Close | `forge_issue_close` | `gh issue close N [--comment]` | `glab issue close N` (comment via separate `note`) |
| Comment | `forge_issue_comment` | `gh issue comment N --body` | `glab issue note N --message` |
| Assign | `forge_issue_assign` | `gh issue edit N --add-assignee` | `glab issue update N --assignee` |
| Label | `forge_issue_label` | `gh issue edit N --add-label` | `glab issue update N --label` |

### Pull Requests / Merge Requests

| Operation | `forge.sh` function | `gh` command | `glab` command |
|---|---|---|---|
| Create | `forge_pr_create` | `gh pr create --title --body --base [--draft]` | `glab mr create --title --description --target-branch [--draft] --no-editor` |
| List | `forge_pr_list` | `gh pr list --state --head --json` | `glab mr list --state --source-branch --output json` |
| View | `forge_pr_view` | `gh pr view N --json` | `glab mr view N --output json` |
| Status | `forge_pr_status` | `gh pr list --head BRANCH --state all --json` | `glab mr list --source-branch BRANCH --all --output json` |
| PR number | `forge_pr_number` | `gh pr list --head BRANCH --json number -q` | JSON parsing from `glab mr list` |
| Merge | `forge_pr_merge` | `gh pr merge N --squash/--rebase [--delete-branch]` | `glab mr merge N [--squash] [--remove-source-branch]` |
| Link issue | `forge_pr_link_issue` | Appends `Closes #N` to PR body | Manual (commit message or MR description) |

### Labels

| Operation | `forge.sh` function | `gh` command | `glab` command |
|---|---|---|---|
| Create (idempotent) | `forge_label_ensure` | `gh label create NAME --color --description` | `glab label create NAME --color --description` |
| List | (via CLI directly) | `gh label list --json name` | `glab label list` |

### Discussions

| Operation | `forge.sh` function | `gh` command | `glab` command |
|---|---|---|---|
| Create | `forge_discussion_create` | Falls back to labeled issue (GraphQL required for real Discussions) | Creates labeled issue (no native equivalent) |

### Projects / Boards

| Operation | `forge.sh` function | `gh` command | `glab` command |
|---|---|---|---|
| List | `forge_project_view` | `gh project list` | `glab board list` |

## Key differences to be aware of

### Body vs Description

- GitHub uses `--body` for issue/PR body text
- GitLab uses `--description` for issue/MR description text

The `forge.sh` functions accept `--body` and translate internally.

### State names

| Concept | GitHub | GitLab |
|---|---|---|
| Open PR/MR | `OPEN` | `opened` |
| Merged PR/MR | `MERGED` | `merged` |
| Closed PR/MR | `CLOSED` | `closed` |

The `forge_pr_status` function normalizes to: `open`, `merged`, `closed`, `none`.

### Assignee

- GitHub: `@me` works as a shortcut for the authenticated user
- GitLab: `@me` may not work in older `glab` versions; use actual username

### JSON output

- GitHub: `--json field1,field2` with `-q` for jq-like queries
- GitLab: `--output json` (returns full object, no field selection)

## Escape hatches

When the abstraction doesn't cover a case, call the CLI directly:

```bash
# Source the library to get FORGE_TYPE
source scripts/forge.sh
forge_detect

case "$FORGE_TYPE" in
  github)
    gh api repos/{owner}/{repo}/discussions ...
    ;;
  gitlab)
    glab api projects/:id/issues ...
    ;;
esac
```

The library sets `FORGE_TYPE` and `FORGE_CLI` so downstream scripts can
branch without re-detecting.

## Adding support for other forges

The detection in `forge_detect` can be extended for:

- **Gitea / Forgejo**: match `gitea.` or check for Gitea API
- **Bitbucket**: match `bitbucket.org`
- **Azure DevOps**: match `dev.azure.com`

Each would need a CLI mapping (e.g., `tea` for Gitea). The library
architecture supports this via the `case "$FORGE_TYPE"` pattern.
