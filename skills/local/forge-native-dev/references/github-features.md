# GitHub Features for Issue-Driven Development

How to leverage GitHub's platform features beyond Issues and PRs.

## GitHub Discussions

Discussions are threaded conversations that live outside the issue tracker.
Use them for:

- Design proposals and trade-off analysis
- Research notes that benefit from collaboration
- Questions and answers (community support)
- Announcements and status updates

### Setup

Enable in **Settings > Features > Discussions**.

### Categories (recommended)

| Category | Use for |
|---|---|
| General | Open-ended discussions |
| Ideas | Feature brainstorming before it becomes an issue |
| Design | Architecture decisions, trade-off analysis |
| Q&A | Questions that have answers (mark as answered) |
| Show and Tell | Demos, progress updates |

### From the CLI

GitHub Discussions creation requires the GraphQL API:

```bash
# List discussions
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      discussions(first: 10) {
        nodes { number title category { name } }
      }
    }
  }
'
```

The `forge_discussion_create` function falls back to creating a labeled
issue because the CLI doesn't have a native `gh discussion create` yet.
Use the web UI for full Discussion features.

### Linking Discussions to Issues

When a Discussion matures into actionable work, create an Issue from it:

```bash
bash scripts/forge-issue.sh create \
  --title "Implement OAuth (from Discussion #15)" \
  --body "Design decided in Discussion #15. Proceeding with approach B.

See: https://github.com/owner/repo/discussions/15" \
  --label "type/feature"
```

## GitHub Projects (v2)

Projects provide Kanban boards, tables, and roadmap views.

### Setup

Create a project from the **Projects** tab or via CLI:

```bash
gh project create --title "Backlog" --owner @me
```

### Recommended views

1. **Board view**: columns by status (Backlog, In Progress, In Review, Done)
2. **Table view**: sortable by priority, assignee, labels
3. **Roadmap view**: timeline by milestone (if using milestones)

### Linking Issues to Projects

```bash
# Add an issue to a project
gh project item-add PROJECT_NUMBER --owner @me --url ISSUE_URL
```

### Automation

GitHub Projects support built-in automations:
- Auto-add Issues when created with specific labels
- Auto-move to "In Progress" when a branch is created
- Auto-move to "Done" when PR is merged

Configure in **Project Settings > Workflows**.

## GitHub Wiki

Wikis are git-backed documentation pages. Use for:

- Long-form documentation that doesn't fit in `docs/`
- Knowledge base articles
- Onboarding guides

### Caveats

- Wikis are a separate git repo (`repo.wiki.git`)
- No PR review process for wiki changes
- Limited formatting compared to GitHub Pages
- Not available on free private repos

### Recommendation

For most projects, prefer `docs/` in the repo (reviewed via PR) over Wiki.
Use Wiki only when you need collaborative editing without PR overhead.

## GitHub Actions integration

### Issue-triggered workflows

```yaml
on:
  issues:
    types: [opened, labeled]

jobs:
  triage:
    if: contains(github.event.issue.labels.*.name, 'agent-task')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Process agent task
        run: echo "Issue #${{ github.event.issue.number }} ready for agent"
```

### PR-triggered workflows

```yaml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run checks
        run: make validate
```

### Scheduled cleanup

```yaml
on:
  schedule:
    - cron: '0 3 * * 1'  # Weekly Monday 3am UTC

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: List stale branches
        run: |
          gh pr list --state merged --json headRefName \
            -q '.[].headRefName' | while read branch; do
            echo "Merged PR branch: $branch"
          done
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## GitHub Releases

Auto-generate release notes from merged PRs:

```bash
git tag -a v1.2.0 -m "release: v1.2.0"
git push origin v1.2.0
gh release create v1.2.0 --generate-notes
```

GitHub groups PRs by label (`feature`, `bug`, `documentation`, etc.)
in the release notes. Use consistent labels for clean releases.

## Useful `gh` commands for daily work

```bash
# Dashboard: your issues and PRs across all repos
gh status

# Quick issue search
gh issue list --search "pagination in:title"

# View PR checks
gh pr checks

# Browse repo in browser
gh repo view --web

# Create a release from the latest tag
gh release create $(git describe --tags --abbrev=0) --generate-notes
```
