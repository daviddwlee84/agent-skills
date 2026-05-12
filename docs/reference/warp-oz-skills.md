# Warp Oz skills

[Warp](https://github.com/warpdotdev/warp) (57k⭐) is a terminal that evolved into an
"agentic development environment." In May 2026 Warp open-sourced its main
codebase under **AGPL-3.0**. Alongside the main repo, the team publishes
[`warpdotdev/oz-skills`](https://github.com/warpdotdev/oz-skills) (764⭐)
— a growing collection of skills for their **Oz** cloud-agent platform.

## Why oz-skills is installable here

oz-skills is **MIT-licensed** and follows the
[agentskills.io specification](https://agentskills.io/specification), so
the skills work in any compliant agent: Claude Code, Codex, OpenCode, Cursor,
Gemini CLI. The Warp agent is just another host — the skills themselves are
portable markdown.

The Warp main repo is AGPL-3.0 (viral copyleft); that license does **not**
propagate to oz-skills, which is separately MIT. Vendoring oz-skills into this
repo is safe.

## Skills we vendor (6 of 15)

We pick skills that fill genuine gaps in this repo's existing lineup. Skipped
skills: `mcp-builder` (duplicate of `anthropics/mcp-builder`), `webapp-testing`
(duplicate of `anthropics/webapp-testing` in the `fullstack-nextjs` series),
`scheduler` (too narrow — local-only reminders), `slack-qa-investigate` (Slack
dependency), `dbt-model-index` / `analysis-artifacts` (BigQuery-shaped for
Warp's internal stack), `terraform-style-check` (too narrow), `seo-aeo-audit`
(too opinionated), `docs-update` (overlaps `doc-coauthoring` / the doc-update
pattern already in CLAUDE.md).

### `github-workflow` plugin — 4 skills

| Skill | Description |
|---|---|
| `ci-fix` | Diagnose GitHub Actions failures: inspect logs via `gh`, identify root cause, implement a minimal fix, push to a dedicated fix branch. Prerequisite: `gh auth status`. |
| `create-pull-request` | Create a well-structured PR following project conventions — commit analysis, branch management, PR body via `gh pr create`. |
| `github-bug-report-triage` | Evaluate a GitHub bug issue for actionability. Locates the project's bug-report template, checks required fields, and drafts a constructive comment for incomplete reports. |
| `github-issue-dedupe` | Detect duplicate issues using multi-strategy semantic + keyword search. Can run manually or be wired into a GitHub Actions workflow. |

These complement `engineering-fundamentals/triage` (mattpocock) which is more
general-purpose. The Oz skills are GitHub-specific and use the `gh` CLI for
automation.

### `web-quality` plugin — 2 skills

| Skill | Description |
|---|---|
| `web-accessibility-audit` | WCAG 2.0/2.1/2.2 compliance audit — identifies violations by POUR principle category, provides remediation steps. Works without an MCP dependency. |
| `web-performance-audit` | Core Web Vitals + Lighthouse audit using the `chrome-devtools` MCP. Requires `chrome-devtools-mcp@latest` configured in `.mcp.json`. If not configured, the skill tells you how to add it. |

`web-accessibility-audit` is MCP-free and works anywhere. `web-performance-audit`
requires the Chrome DevTools MCP — the skill gracefully degrades if it is not
present.

## Install

```bash
# All 6 via this repo
npx skills@latest add daviddwlee84/agent-skills

# Or directly from upstream
npx skills@latest add warpdotdev/oz-skills/.agents/skills/ci-fix
npx skills@latest add warpdotdev/oz-skills/.agents/skills/web-accessibility-audit
# ...
```

## Warp's AGPL-3.0 note

The Warp terminal itself is AGPL-3.0. If you embed Warp into a product you
ship to users, AGPL requires you to open-source your modifications. Using Warp
as a local development tool does not trigger AGPL. Using oz-skills (MIT)
separately from Warp has no AGPL implications.

## See also

- [Browser automation skills](browser-automation-skills.md) — testing web apps
  in a real browser; complements the web-quality skills above
- [`fullstack-nextjs/webapp-testing`](../skills/webapp-testing.md) — the
  Playwright-based Anthropic skill already vendored for frontend QA
- [Agent skill compatibility](agent-skill-compatibility.md) — portable
  `SKILL.md` spec all these skills follow
