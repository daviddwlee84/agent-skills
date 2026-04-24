# webapp-testing (vendored)

Vendored from
[anthropics/skills/skills/webapp-testing](https://github.com/anthropics/skills/tree/main/skills/webapp-testing)
(part of the [`fullstack-nextjs`](index.md#fullstack-nextjs-series) series).
Synced via [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile);
do not edit
[`skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md)
locally — changes will be clobbered on the next sync.

## Upstream frontmatter description

> Toolkit for interacting with and testing local web applications using
> Playwright. Supports verifying frontend functionality, debugging UI
> behavior, capturing browser screenshots, and viewing browser logs.

## What it teaches

Native Python Playwright workflow with a `scripts/with_server.py` helper
that manages server lifecycle (multiple servers supported). Decision tree:
static HTML → read selectors directly; dynamic webapp → use the helper +
write a simplified Playwright script. Black-box scripts run with `--help`
first to keep them out of the context window.

## Related fullstack-nextjs skills

- [`nextjs`](nextjs.md) — the dev server that webapp-testing drives
- [`frontend-design`](frontend-design.md) — close the loop: build → screenshot → critique

## Canonical SKILL.md

See
[skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/fullstack-nextjs/webapp-testing/SKILL.md)
for the full instructions. Upstream source:
[anthropics/skills](https://github.com/anthropics/skills).
