# GitLab Features for Issue-Driven Development

How to leverage GitLab's platform features beyond Issues and Merge Requests.

## GitLab Boards

Boards provide Kanban-style visualization of issues.

### Default board

Every project has a default board with "Open" and "Closed" lists.

### Custom boards

Create label-based lists to mirror the priority workflow:

```bash
# Create board lists (via web UI or API)
glab board list
```

Recommended lists:
- **Backlog** (label: `backlog`)
- **P1 — Critical** (label: `priority/P1`)
- **P2 — Medium** (label: `priority/P2`)
- **In Progress** (label: `in-progress`)
- **Review** (linked to open MRs)

### Scoped boards

Create multiple boards for different views:
- **Sprint board**: current iteration issues
- **Bug triage board**: `type/bug` issues by priority
- **Agent work board**: `agent-task` issues

## GitLab Issue Threads

GitLab doesn't have GitHub-style Discussions, but issue threads serve a
similar purpose:

- **Threaded comments** on issues for design discussions
- **Issue links** (related, blocking, blocked by) for dependency tracking
- **Weight** field for effort estimation (maps to S/M/L/XL)

### Design discussions in issues

Create a dedicated issue for design discussion:

```bash
bash scripts/forge-issue.sh create \
  --title "[Design] Authentication architecture" \
  --body "## Options

### Option A: JWT + refresh tokens
...

### Option B: Session-based auth
...

## Decision criteria
..." \
  --label "discussion"
```

### Issue weights

GitLab supports numeric weights on issues:

| forge-native-dev effort | GitLab weight |
|---|---|
| S | 1 |
| M | 3 |
| L | 8 |
| XL | 13 |

```bash
glab issue update 42 --weight 3
```

## GitLab Epics (Premium/Ultimate)

Epics group related issues across milestones:

- An epic = a large feature or initiative
- Issues within the epic = individual work items
- Roadmap view shows epic timelines

For free-tier GitLab, use milestones instead.

## GitLab Milestones

Group issues by time-boxed iterations:

```bash
# Create a milestone
glab api projects/:id/milestones -f title="v1.0" -f due_date="2027-01-01"

# Assign issue to milestone
glab issue update 42 --milestone "v1.0"
```

## GitLab CI/CD Integration

### MR-triggered pipelines

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test

validate:
  stage: validate
  rules:
    - if: $CI_MERGE_REQUEST_IID
  script:
    - make validate

test:
  stage: test
  rules:
    - if: $CI_MERGE_REQUEST_IID
  script:
    - make test
```

### Issue-triggered pipelines (via API)

```yaml
# Trigger pipeline when issue is labeled
issue_dispatch:
  rules:
    - if: $CI_PIPELINE_SOURCE == "trigger"
  variables:
    ISSUE_NUMBER: $TRIGGER_ISSUE
  script:
    - echo "Processing issue #$ISSUE_NUMBER"
```

### Scheduled cleanup

```yaml
cleanup:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  script:
    - |
      glab mr list --state merged --output json | \
        python3 -c "import json,sys; [print(mr['source_branch']) for mr in json.load(sys.stdin)]"
```

## Merge Request features

### MR templates

Place templates in `.gitlab/merge_request_templates/`:

```markdown
<!-- .gitlab/merge_request_templates/Default.md -->
## Summary

Closes #ISSUE_NUMBER

## Changes

- ...

## Testing

- [ ] Unit tests pass
- [ ] Manual testing done

## Checklist

- [ ] Code follows project conventions
- [ ] Documentation updated (if needed)
```

### MR approvals (Premium)

Configure approval rules in **Settings > Merge requests**:
- Require N approvals before merge
- Designate code owners per path

### Merge trains

GitLab merge trains run CI on the combined result of queued MRs:

```yaml
merge_train:
  rules:
    - if: $CI_MERGE_REQUEST_EVENT_TYPE == "merge_train"
  script:
    - make test
```

## Useful `glab` commands for daily work

```bash
# Dashboard: your MRs and issues
glab mr list --assignee @me
glab issue list --assignee @me

# Quick issue search
glab issue list --search "pagination"

# View MR pipeline status
glab ci status

# Browse repo in browser
glab repo view --web

# Create a release
glab release create v1.2.0 --notes "Release notes..."
```

## GitLab vs GitHub feature mapping

| Feature | GitHub | GitLab |
|---|---|---|
| Issues | Issues | Issues |
| PRs | Pull Requests | Merge Requests |
| Discussions | Discussions | Issue threads |
| Projects | Projects (v2) | Boards |
| Wiki | Wiki | Wiki |
| CI/CD | Actions | GitLab CI/CD |
| Releases | Releases | Releases |
| Code owners | CODEOWNERS | CODEOWNERS |
| Branch protection | Branch rules | Protected branches |
| Effort tracking | Labels | Issue weights |
| Epics | Milestones | Epics (Premium) / Milestones |
