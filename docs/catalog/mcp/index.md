# MCP wiki

A personal-knowledge area for [Model Context Protocol](https://modelcontextprotocol.io/)
servers we've evaluated, use, or want to track. Modeled after
[Karpathy's LLM Wiki pattern](../../reference/llm-wiki-pattern.md) — each
entry is a curated record, not a vendored install target.

## Entries

| Name | Domain | Status | Auth | Hosting |
|---|---|---|---|---|
| [Financial Datasets MCP](financialdatasets-ai.md) | [Finance](../domains/finance.md) / [Quant Research](../domains/quant-research.md) | `wishlist` | OAuth 2.1 + API key | Hosted (`mcp.financialdatasets.ai`) |

## Why a wiki, not a registry?

A registry needs an opinion on every MCP and a curation team. A wiki is
just notes the maintainer wants to keep. The value is in *recording the
decision* (use it, skip it, defer it, why) so future-you doesn't
re-research the same MCP.

This wiki is intentionally aligned with the
[LLM Wiki pattern](../../reference/llm-wiki-pattern.md) — pages are written
by hand for now (small N), with frontmatter that future automation can
parse to regenerate the index table.

## Per-entry conventions

Every MCP entry is one markdown file under `docs/catalog/mcp/<slug>.md`,
with required YAML frontmatter:

```yaml
---
name: <human-readable name>
slug: <kebab-case slug, matches filename>
upstream_url: <docs URL>
transport: HTTP | stdio | SSE | mixed
auth: <one-line description>
hosting: Hosted (<host>) | Local | Self-hosted
domain: <one of the domain hub slugs>
status: vendored | deferred | skipped | evaluated | wishlist
license: <SPDX or "Proprietary">
last_verified: <YYYY-MM-DD>
---
```

The page body follows a consistent structure:

1. **TL;DR** (2 sentences)
2. **Tools / capabilities** (table, ~6-12 rows)
3. **Auth & install** (one snippet per host: Claude Code, Claude Desktop, Cursor, Managed Agents)
4. **When to use it / When NOT to use it** (paired bullets)
5. **Related skills in this repo** (cross-links to `docs/skills/*` or domain hubs)
6. **Upstream sources** (1-3 links — docs / GitHub / blog post)

The `status` field uses the same enum as
[external skill entries](../skill-collections.md) — see the snippet at
the top of any catalog page for the full enum table.

## See also

- [LLM Wiki pattern](../../reference/llm-wiki-pattern.md) — Karpathy's
  pattern this wiki is modeled after.
- [Domains](../domains/index.md) — each domain hub lists relevant MCPs.
- Upstream MCP directory: [modelcontextprotocol.io/servers](https://github.com/modelcontextprotocol/servers).
