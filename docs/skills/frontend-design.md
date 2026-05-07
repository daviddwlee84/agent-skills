# frontend-design (vendored)

Vendored from
[anthropics/skills/skills/frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/frontend-design/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/frontend-design/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Create distinctive, production-grade frontend interfaces with high design
> quality. Use this skill when the user asks to build web components, pages,
> artifacts, posters, or applications (examples include websites, landing
> pages, dashboards, React components, HTML/CSS layouts, or when
> styling/beautifying any web UI). Generates creative, polished code and
> UI design that avoids generic AI aesthetics.

## What it teaches

Aesthetic direction skill — encourages a bold, intentional point of view
(brutally minimal, maximalist, retro-futuristic, editorial, …) and refined
typography choices instead of default Inter/Arial. Anti-AI-slop guardrails.
Use as the creative counterpart to [`web-design-guidelines`](web-design-guidelines.md)'s
audit role.

## Related fullstack-nextjs skills

- [`shadcn`](shadcn.md) — components to express the chosen aesthetic
- [`web-design-guidelines`](web-design-guidelines.md) — a11y/perf audit after the look is in
- [`webapp-testing`](webapp-testing.md) — Playwright loop to verify the result visually

## Also published as a Claude Code plugin

The same skill is republished as the
[`frontend-design`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design)
plugin on the
[`claude-plugins-official`](https://github.com/anthropics/claude-plugins-official)
marketplace, which is why Claude Code's startup tip sometimes recommends
`/plugin install frontend-design@claude-plugins-official`. **Do not install it
on top of the vendored copy** — both pull from the same source; the only
difference is the frontmatter `description` line, and the `anthropics/skills`
upstream we vendor from has richer trigger phrasing (mentions artifacts,
posters, landing pages, dashboards, and HTML/CSS layouts in addition to
components/pages/applications).

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/frontend-design/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/frontend-design/SKILL.md)
for the full instructions. Upstream source:
[anthropics/skills](https://github.com/anthropics/skills).
