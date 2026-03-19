# Agent Skills

- [Overview - Agent Skills](https://agentskills.io/home)

A personal collection of agent skills — both custom-authored and cherry-picked from upstream repos — installable as a single package.

## Getting Started

```bash
npx skills@latest add daviddwlee84/agent-skills
```

## Structure

```
skills/
  local/           # Custom skills authored by us
  vendor/          # 3rd-party skills synced from upstream repos
vendor.yaml        # Manifest tracking upstream sources
scripts/
  sync-vendor.sh   # Sync script for vendored skills
Makefile           # Convenience targets
```

## Available Skills

### Local

| Skill | Description |
|-------|-------------|
| [quantatitive-factor-researcher](skills/local/quantatitive-factor-researcher/) | Quantitative factor research assistant |

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

2. Run `make sync` (requires `gh` and `yq`)

### Check for upstream updates

```bash
make sync-check
```

## Resources

### Skills Manager

- [vercel-labs/skills: The open agent skills tool - npx skills](https://github.com/vercel-labs/skills)
- [Skill.Fish - Skill manager for AI coding agents](https://www.skill.fish/)
  - [knoxgraeme/skillfish: The skill manager for AI coding agents. Install, update, and sync skills across Claude Code, Cursor, Copilot + more.](https://github.com/knoxgraeme/skillfish)

### Skills

- [vercel-labs/agent-skills: Vercel's official collection of agent skills](https://github.com/vercel-labs/agent-skills/tree/main)
- [marimo-team/skills: skills for coding agents related to marimo](https://github.com/marimo-team/skills)
- [mattpocock/skills: My personal directory of skills, straight from my .claude directory.](https://github.com/mattpocock/skills)

---

Good to be skills:

- [humanlayer/12-factor-agents: What are the principles we can use to build LLM-powered software that is actually good enough to put in the hands of production customers?](https://github.com/humanlayer/12-factor-agents)
- [The Twelve-Factor App](https://12factor.net/)
