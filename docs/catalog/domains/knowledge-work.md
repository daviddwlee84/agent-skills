# Knowledge Work

Job-function plugins for sales / legal / customer support / product
management / marketing / data / etc. Driven primarily by Anthropic's
[Knowledge Work Plugins](https://github.com/anthropics/knowledge-work-plugins)
program. This hub is mostly a registry today — we don't ship local skills
in this space, but track external offerings for future use.

## Skills in this repo

### Local

| Skill | One-line | Notes |
|---|---|---|
| _none yet_ | | This repo focuses on engineering / ML / docs tooling. Knowledge-work plugins are job-function-shaped and overlap less with the maintainer's day-to-day. |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _none yet_ | | |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

The full Anthropic Knowledge Work Plugins marketplace (11 plugins, MIT
licensed). Each is a Cowork / Claude Code plugin bundling skills + slash
commands + MCP connectors specific to a job function.

| Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| `productivity` | [knowledge-work-plugins/productivity](https://github.com/anthropics/knowledge-work-plugins/tree/main/productivity) | `wishlist` | Generic task / calendar / workflow plugin. Slack + Notion + Asana + Linear + Jira + Monday + ClickUp + Microsoft 365 connectors. | `claude plugin install productivity@knowledge-work-plugins` |
| `sales` | [`.../sales`](https://github.com/anthropics/knowledge-work-plugins/tree/main/sales) | `wishlist` | Prospect research, call prep, pipeline review. | `claude plugin install sales@knowledge-work-plugins` |
| `customer-support` | [`.../customer-support`](https://github.com/anthropics/knowledge-work-plugins/tree/main/customer-support) | `wishlist` | Ticket triage, escalations, KB articles. | `claude plugin install customer-support@knowledge-work-plugins` |
| `product-management` | [`.../product-management`](https://github.com/anthropics/knowledge-work-plugins/tree/main/product-management) | `wishlist` | Specs, roadmaps, user research, competitive tracking. | `claude plugin install product-management@knowledge-work-plugins` |
| `marketing` | [`.../marketing`](https://github.com/anthropics/knowledge-work-plugins/tree/main/marketing) | `wishlist` | Content, campaigns, brand voice, performance reporting. | `claude plugin install marketing@knowledge-work-plugins` |
| `legal` | [`.../legal`](https://github.com/anthropics/knowledge-work-plugins/tree/main/legal) | `wishlist` | Contract review, NDAs, compliance, risk assessment. | `claude plugin install legal@knowledge-work-plugins` |
| `finance` | [`.../finance`](https://github.com/anthropics/knowledge-work-plugins/tree/main/finance) | `wishlist` | Journal entries, reconciliation, financial statements, audits. Cross-listed in [Finance](finance.md) hub. | `claude plugin install finance@knowledge-work-plugins` |
| `data` | [`.../data`](https://github.com/anthropics/knowledge-work-plugins/tree/main/data) | `wishlist` | SQL queries, visualization, statistical analysis, dashboards. Snowflake + Databricks + BigQuery connectors. | `claude plugin install data@knowledge-work-plugins` |
| `enterprise-search` | [`.../enterprise-search`](https://github.com/anthropics/knowledge-work-plugins/tree/main/enterprise-search) | `wishlist` | Cross-tool search across email / chat / docs / wikis. | `claude plugin install enterprise-search@knowledge-work-plugins` |
| `bio-research` | [`.../bio-research`](https://github.com/anthropics/knowledge-work-plugins/tree/main/bio-research) | `wishlist` | Cross-listed in [AI/ML Research](ai-ml-research.md) hub. | `claude plugin install bio-research@knowledge-work-plugins` |
| `cowork-plugin-management` | [`.../cowork-plugin-management`](https://github.com/anthropics/knowledge-work-plugins/tree/main/cowork-plugin-management) | `wishlist` | Meta-plugin for organizations creating their own plugins. | `claude plugin install cowork-plugin-management@knowledge-work-plugins` |

Marketplace bootstrap (one-time, then install any of the above):

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
```

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| _none surveyed yet_ — most knowledge-work plugins bundle MCP connectors directly in `.mcp.json` | | | | |

## Backlog (TODO `P?` items)

- _none yet — open a TODO `P?` if you want to evaluate a specific plugin._

## See also

- [Finance](finance.md) — has overlap with `finance` and `data` plugins.
- [AI/ML Research](ai-ml-research.md) — cross-lists `bio-research`.
- Upstream README: [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) — full plugin matrix + connector list.
