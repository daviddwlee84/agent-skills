# Agent Skills

- [Overview - Agent Skills](https://agentskills.io/home)

A personal collection of agent skills — both custom-authored and cherry-picked from upstream repos — installable as a single package.

## Getting Started

```bash
# NOTE: If use daviddwlee84/agent-skills will only find skills in .agents/skills
npx skills@latest add daviddwlee84/agent-skills/skills

# Render the repo backlog as a validated kanban-style board
make kanban
```

## Structure

```txt
.agents/           # Agent config that used for this repo
TODO.md            # Future work index plus recent shipped items
backlog/           # Deferred investigation linked from TODO.md
pitfalls/          # Past non-obvious traps and their fixes
skills-lock.json   # npx skills managed skills for this repo
skills/
  local/           # Custom skills authored by us
  vendor/          # 3rd-party skills synced from upstream repos
vendor.yaml        # Manifest tracking upstream sources
scripts/
  add-vendor.sh      # Add 3rd-party skills
  sync-vendor.sh     # Sync script for vendored skills
  todo-kanban.sh     # Validate TODO.md and render kanban-style board
  promote-todo.sh    # Move an active TODO item to ## Done with re-validation
Makefile           # Convenience targets
```

## Roadmap & lessons learned

Forward-looking work lives in [`TODO.md`](TODO.md), grouped into `P1` through
`P3` plus `P?` for ideas that still need evaluation. Non-trivial investigation
or paused analysis should be linked from the TODO entry into
[`backlog/`](backlog/).

Backward-looking knowledge lives in [`pitfalls/`](pitfalls/), titled by
symptom so humans and agents can grep recurring issues quickly. Recent shipped
work stays in `TODO.md` under `## Done` until it is large enough to prune into a
future `CHANGELOG.md`.

To render a validated board view for the current backlog, run `make kanban` or
[`./scripts/todo-kanban.sh`](scripts/todo-kanban.sh). When implementing a TODO
item, run [`./scripts/promote-todo.sh`](scripts/promote-todo.sh) so the move
into `## Done` is atomic and re-validated.

Both scripts originate from
[`skills/local/project-knowledge-harness`](skills/local/project-knowledge-harness/);
applying that skill to another project is a one-shot via
`skills/local/project-knowledge-harness/scripts/init.sh --target /path/to/repo`.

## Available Skills

Local skills are documented in detail under [`docs/`](docs/) — what each
skill is for, when it triggers, and how to use any bundled scripts.

### Local

| Skill | Description | Detailed doc |
|-------|-------------|--------------|
| [quantatitive-factor-researcher](skills/local/quantatitive-factor-researcher/) | Quantitative factor research assistant | [docs](docs/quantatitive-factor-researcher.md) |
| [project-knowledge-harness](skills/local/project-knowledge-harness/) | Set up TODO.md + backlog/ + pitfalls/ structure for project memory, plus a bundled init / kanban / promote toolkit | [docs](docs/project-knowledge-harness.md) |

### Vendored

| Skill | Upstream |
|-------|----------|
| [marimo-notebook](skills/vendor/marimo-notebook/) | [marimo-team/skills](https://github.com/marimo-team/skills) |

## Adding Skills

### Add a new local skill

```bash
cd skills/local
npx skills@latest init [skill-name]
```

### Add a new vendored skill

#### Quick Script

```bash
# Similar to: npx skills add owner/repo/path/to/skill
./scripts/add-vendor.sh owner/repo/path/to/skill

# Examples
./scripts/add-vendor.sh marimo-team/skills/skills/marimo-notebook
./scripts/add-vendor.sh vercel-labs/agent-skills/skills/next-js
./scripts/add-vendor.sh --name my-name --branch dev owner/repo/skills/some-skill

# Or via Makefile
make add-vendor SOURCE=owner/repo/path/to/skill

# GitHub URLs also work
./scripts/add-vendor.sh https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook
```

This verifies the upstream path exists, adds an entry to `vendor.yaml`, and syncs the skill immediately.

Use `--no-sync` to only add the entry without downloading.

**Dependencies:** `gh` (GitHub CLI, authenticated) and `yq` (YAML processor)

#### Config File

1. Add an entry to `vendor.yaml`:

```yaml
  - name: my-skill
    upstream:
      owner: org-name
      repo: skills-repo
      path: skills/my-skill
      branch: main
    last_sync:
      date: ""
      commit: ""
```

1. Run `make sync` (requires `gh` and `yq`)

#### Check for upstream updates

```bash
make sync-check
```

## Resources

### Skills Manager

- [vercel-labs/skills: The open agent skills tool - npx skills](https://github.com/vercel-labs/skills)
  - [The Agent Skills Directory](https://skills.sh/)
- [Skill.Fish - Skill manager for AI coding agents](https://www.skill.fish/)
  - [knoxgraeme/skillfish: The skill manager for AI coding agents. Install, update, and sync skills across Claude Code, Cursor, Copilot + more.](https://github.com/knoxgraeme/skillfish)

### Skills

#### Skill Set

General

- [vercel-labs/agent-skills: Vercel's official collection of agent skills](https://github.com/vercel-labs/agent-skills/tree/main)
- [mattpocock/skills: My personal directory of skills, straight from my .claude directory.](https://github.com/mattpocock/skills)
- [anthropics/skills: Public repository for Agent Skills](https://github.com/anthropics/skills)
- [anthropics/knowledge-work-plugins: Open source repository of plugins primarily intended for knowledge workers to use in Claude Cowork](https://github.com/anthropics/knowledge-work-plugins/tree/main)

For Specific Framework

- [marimo-team/skills: skills for coding agents related to marimo](https://github.com/marimo-team/skills)
- [streamlit/agent-skills: A collection of agent skills for development of Streamlit apps.](https://github.com/streamlit/agent-skills)

Single Skill

- [FrancyJGLisboa/agent-skill-creator: Turn any workflow into reusable AI agent skills that install on 14+ tools — Claude Code, Copilot, Cursor, Windsurf, Codex, Gemini, Kiro, and more. One SKILL.md, every platform.](https://github.com/FrancyJGLisboa/agent-skill-creator)
- [find-skills by vercel-labs/skills](https://skills.sh/vercel-labs/skills/find-skills)

### Collections

- [RKiding/Awesome-finance-skills: A collection of Awesome Finance Agent Skills for free and easy to start | 一系列开源免费的金融分析Agent Skills](https://github.com/RKiding/Awesome-finance-skills)
- [Orchestra-Research/AI-Research-SKILLs: Comprehensive open-source library of AI research and engineering skills for any AI model. Package the skills and your claude code/codex/gemini agent will be an AI research agent with full horsepower. Maintained by Orchestra Research.](https://github.com/Orchestra-Research/AI-research-SKILLs)

### Articles

- [Six skills for financial service professionals | Claude](https://claude.com/resources/tutorials/claude-for-financial-services-skills)
  - [Financial services | Claude by Anthropic](https://claude.com/solutions/financial-services)
- [Building Agent Skills with skill-creator | by Daniela Petruzalek | Google Cloud - Community | Feb, 2026 | Medium](https://medium.com/google-cloud/building-agent-skills-with-skill-creator-855f18e785cf)
- [Introducing: React Best Practices - Vercel](https://vercel.com/blog/introducing-react-best-practices)
  - [agent-skills/skills/react-best-practices at main · vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)

---

Good to be skills:

- [humanlayer/12-factor-agents: What are the principles we can use to build LLM-powered software that is actually good enough to put in the hands of production customers?](https://github.com/humanlayer/12-factor-agents)
- [The Twelve-Factor App](https://12factor.net/)
