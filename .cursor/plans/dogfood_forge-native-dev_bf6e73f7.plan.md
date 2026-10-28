---
name: dogfood forge-native-dev
overview: "Dogfood forge-native-dev on this repo: enable Discussions with recommended categories, create a GitHub Project board (with Board/Table/Roadmap views), migrate TODO.md P2+P3 items to Issues and P? items to Discussions, slim down TODO.md to a pointer file, update forge-init.sh with project board setup, and fix standalone-usage gaps in the skill."
todos:
  - id: prereqs
    content: Re-auth gh with project scope, enable Discussions on the repo, create Discussion categories via web UI
    status: completed
  - id: project-board
    content: Create GitHub Project board with Status columns (Backlog/Todo/In Progress/In Review/Done/Not Planned), custom fields (Priority/Effort/Target Date), views (Board/Table/Roadmap), and automations
    status: completed
  - id: migrate-p2-p3
    content: Migrate 2 P2 + 12 P3 items from TODO.md to GitHub Issues with appropriate labels, linking backlog/ docs where they exist
    status: completed
  - id: migrate-p-question
    content: Migrate ~20 P? items to Discussions (Ideas category), grouping related evaluations and linking existing backlog/ research docs
    status: completed
  - id: slim-todo-md
    content: Transform TODO.md into a pointer file (links to Issues/Discussions/Project), preserve Done history, update AGENTS.md guidance block
    status: completed
  - id: conventions-ref
    content: Add references/conventions.md to forge-native-dev covering commit format, branch naming, merge strategy (standalone, no git-workflow dependency)
    status: completed
  - id: issue-vs-discussion
    content: Add Issue vs Discussion content boundary guidance to SKILL.md and references/issue-driven-workflow.md
    status: completed
  - id: post-merge-guidance
    content: Add post-merge follow-up best practice (new branch, new PR) to the skill docs
    status: completed
  - id: project-setup-script
    content: Add forge_project_create to forge.sh and --setup-project flag to forge-init.sh; update gitlab-features.md with Board/Milestone equivalents
    status: completed
isProject: false
---

# Dogfood forge-native-dev on agent-skills

## Pre-requisites

The `gh` token currently lacks `read:project` scope. Before any project
operations, run:

```bash
gh auth refresh -s read:project,project
```

## Phase 1: Enable GitHub features and create Project board

### 1a. Enable Discussions

Enable via `gh api` (or web UI):

```bash
gh repo edit --enable-discussions
```

Create recommended Discussion categories:

- **Ideas** — "should we build X?" evaluations, skill proposals (P? items go here)
- **Design** — architecture decisions, trade-off analysis
- **Research** — exploration of external tools, libraries, patterns
- **Q&A** — questions about skill authoring, installation, usage
- **General** — everything else

Note: Discussion categories must be created via web UI (Settings > Discussions)
or GraphQL API — `gh` CLI has no `discussion category create` command.

### 1b. Create GitHub Project board

Create the project with `gh project create`:

```bash
gh project create --title "agent-skills Backlog" --owner @me
```

Configure status field with columns:
- **Backlog** — captured, not yet prioritized for work
- **Todo** — prioritized, ready to start
- **In Progress** — actively being worked on
- **In Review** — PR open, awaiting review
- **Done** — shipped
- **Not Planned** — explicitly decided against (instead of deleting)

Add custom fields:
- **Priority** (single-select): P1, P2, P3, P?
- **Effort** (single-select): S, M, L, XL
- **Target Date** (date): optional, for Roadmap view

Create views:
- **Board** (default): grouped by Status
- **Table**: sortable by Priority, Effort, Status
- **Roadmap**: timeline view filtered to items with Target Date set

Set up built-in automations:
- Item added → Status: Backlog
- Issue closed → Status: Done
- PR merged → Status: Done
- Issue reopened → Status: In Progress

### 1c. Add project setup to forge-init.sh

Add a `--setup-project` flag to [`scripts/forge-init.sh`](skills/local/forge-native-dev/scripts/forge-init.sh):

```bash
forge-init.sh --setup-project --target /path/to/project
```

This requires:
- Add `forge_project_create` to [`scripts/forge.sh`](skills/local/forge-native-dev/scripts/forge.sh)
  (GitHub: `gh project create` + `gh project field-create` + `gh project view-create`;
  GitLab: `glab` has no board-create CLI — document manual steps)
- The function should be idempotent (skip if project already exists)
- Note: GitHub Projects v2 API is GraphQL-heavy; the `gh project` subcommands
  abstract most of it but require the `project` scope

GitLab equivalent: Boards + Milestones. Document the mapping in
[`references/gitlab-features.md`](skills/local/forge-native-dev/references/gitlab-features.md):
- Board lists = Status columns (created via web UI or API)
- Milestones = time-boxed groupings (no Gantt, but a progress bar)
- No native Roadmap/Gantt view — suggest third-party like Mermaid in issues

## Phase 2: Migrate TODO.md content

### 2a. Migrate P2 items (2) to Issues

Each becomes an Issue with `priority/P2` + `type/chore` labels:

- "Bump GitHub Actions to next majors before Node 20 deprecation" [S]
- "Publish finalization readiness contract for dev-cli" [L] — link to `backlog/publish-finalization-readiness-contract-for-dev-cli.md` in the issue body

### 2b. Migrate P3 items (12) to Issues

Each becomes an Issue with `priority/P3` label. Items with backlog/ research
docs get a link in the issue body. Quick list:

- Document 'prefer relative links' as docs convention [S]
- Mirror-check script for scripts/ vs PKH/scripts/ [S]
- Bake validation.links.not_found:info into mkdocs-site-bootstrap template [M]
- Document --full-depth in README install snippet [S]
- Smoke-test marimo-batch-mlflow starting-point.py [S]
- Offer Tyro + provider-agnostic refactor as upstream PR [S]
- Decide on LLM Wiki skill [M]
- Catalog frontmatter validator script [S]
- MCP wiki index auto-regenerator [S]
- Catalog cross-link audit script [M]
- Migrate task runner from Makefile to Justfile [M]
- sync-check: detect removed upstream paths [S]

### 2c. Migrate P? items (~20) to Discussions (Ideas category)

Each becomes a Discussion in the "Ideas" category. Group related ones
(e.g., all "evaluate X skill" items) into a single Discussion where
sensible to reduce noise. Example groupings:

- **Web framework skills**: Next.js+Supabase, Streamlit, Playwright
- **ML/AI skills**: MLflow, DVC, LLM fine-tuning, HuggingFace, LangChain
- **Infra skills**: Docker Compose, Kubernetes, Terraform, Ansible, CI/CD
- **Standalone evaluations**: Grafana+OTEL, n8n, Rust+PyO3, Discord bot, Tardis SDK, etc.

Items that already have backlog/ research docs (financial-data-sources.md,
flatten-fullstack-nextjs-series.md, evaluate-remaining-mattpocock-skills.md)
get linked from the Discussion body.

### 2d. Cross-referencing

- Issues reference Discussions when relevant: "Design discussion: #D15"
- Discussions reference Issues when work is extracted: "Tracked in #42"
- PRs reference Issues: "Closes #42"
- This three-way linking is the key value of using the forge natively

## Phase 3: Slim down TODO.md

Transform [`TODO.md`](TODO.md) into a pointer file:

```markdown
# TODO

This project uses GitHub Issues as the canonical backlog and GitHub
Discussions for evaluative/research topics.

- **Issues (actionable work)**: https://github.com/daviddwlee84/agent-skills/issues
- **Discussions (ideas/research)**: https://github.com/daviddwlee84/agent-skills/discussions
- **Project board**: https://github.com/users/daviddwlee84/projects/N

Keep `backlog/` and `pitfalls/` in-repo as before.

## Done

(preserve existing Done section as historical record)
```

Remove the PKH guidance block from `AGENTS.md` and replace with the
forge-native-dev guidance block (already partially there from the skill).

## Phase 4: Fix standalone-usage gaps in the skill

Issues found during dogfooding review:

### 4a. Self-contained commit/branch conventions

Users without `git-workflow` installed need minimum guidance. Add a
`references/conventions.md` to forge-native-dev covering:

- Conventional Commits (brief — type: subject format)
- Branch naming (`issue/<N>-<slug>`, `agent/issue/<N>-<slug>`)
- Linear history defaults (`pull.rebase true`, `merge.ff only`)
- Squash merge as default

This avoids silently depending on git-workflow for the basics.

### 4b. Issue vs Discussion content boundary

Add a section to `SKILL.md` and `references/issue-driven-workflow.md`:

- **Issue** = actionable with clear done criteria (can be closed when shipped)
- **Discussion** = open-ended: evaluations, trade-offs, "should we?" questions
- **Promotion**: Discussion matures into actionable work → create an Issue,
  link back to the Discussion
- Keep issue bodies concise — detailed analysis goes in Discussion threads,
  linked from the issue

### 4c. Post-merge follow-up best practice

Add to `SKILL.md` gotchas or `references/issue-driven-workflow.md`:

- After a PR merges, always create a **new branch from updated main** for
  follow-up work
- Do not reuse the merged branch (history diverges after squash)
- Do not try to reopen a merged PR (GitHub does not allow it)
- Each PR is one logical change; follow-ups are new PRs
- Name the branch for the issue it addresses, not the previous PR

### 4d. Update forge_project_create in forge.sh

Add project board creation functions to the library:

- `forge_project_create` — create a project with standard fields/views
- `forge_project_add_item` — add an issue to a project
- Document that this requires `project` scope on the gh token

## Phase 5: Post-merge branch workflow

Since PR #5 is already merged, for this dogfooding work:

1. `git switch main && git pull --rebase`
2. `git switch -c cursor/dogfood-forge-native-dev`
3. Make all changes
4. Push and create new PR (draft)

This is the pattern the skill should recommend: new branch, new PR,
clean separation of concerns.
