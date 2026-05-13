# Finance

Banking, capital markets, equity research, wealth management, fund admin,
and accounting workflows. For trading-strategy / factor-research / backtesting
work, see the [Quant Research](quant-research.md) hub.

## Skills in this repo

### Local

| Skill | One-line | Notes |
|---|---|---|
| _none direct_ | | [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md) is the closest fit but is quant-flavored — see the [Quant Research](quant-research.md) hub. |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _none yet_ | | |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| `claude-for-financial-services` (full marketplace) | [`anthropics/financial-services`](https://github.com/anthropics/financial-services) | `wishlist` | Massive marketplace (11 named agents + 7 vertical plugins + partner plugins). Needs evaluation per-plugin — most assume Cowork / Managed Agents deployment, not solo Claude Code. | `claude plugin marketplace add anthropics/financial-services` then pick a plugin (e.g. `financial-analysis`, `equity-research`, `investment-banking`). |
| `financial-analysis` plugin (subset) | [`anthropics/financial-services/plugins/vertical-plugins/financial-analysis`](https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis) | `wishlist` | Core skills (DCF, LBO, comps, 3-statement) + 11 MCP connectors. Highest-value entry point if vendoring any subset. | `claude plugin install financial-analysis@claude-for-financial-services` |
| `Awesome-finance-skills` curated list | [`RKiding/Awesome-finance-skills`](https://github.com/RKiding/Awesome-finance-skills) | `wishlist` | Eight-skill bundle (news, stock data, sentiment, forecasting, signal tracking, viz, reporting, web search). Plug-and-play for finance-flavored agents. Independent author — verify license + maintenance. | Inspect upstream `SKILL.md` layout, then `npx skills@latest add RKiding/Awesome-finance-skills`. |
| Six skills (Claude for Financial Services) | [Claude tutorial](https://claude.com/resources/tutorials/claude-for-financial-services-skills) | `evaluated` | Toggleable in Settings → Capabilities → Skills (no manual install). Tutorial only — exclusive to Claude for Financial Services accounts. Documents 6 first-party skills: Comps Analysis, DCF, Initiating Coverage Research, Strip Profile, Due Diligence Data Pack, Earnings Analysis. | Not installable via `npx skills`; surfaced in the official Claude UI for FSI accounts. |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| Financial Datasets MCP | [`docs.financialdatasets.ai/mcp-server`](https://docs.financialdatasets.ai/mcp-server) | `wishlist` | OAuth 2.1 + API key | [Per-MCP page](../mcp/financialdatasets-ai.md) |
| LSEG, S&P Global, FactSet, etc. | bundled in `anthropics/financial-services/financial-analysis/.mcp.json` | `wishlist` | Provider-specific | _no per-MCP record yet — add when evaluated_ |

## Backlog (TODO `P?` items)

See the [`P?` lane in `TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md):

- `[?/L]` **Financial data sources skill set** — compare free vs paid market-data providers, regional coverage, organize-by-provider vs by-workflow. → [`backlog/financial-data-sources.md`](https://github.com/daviddwlee84/agent-skills/blob/main/backlog/financial-data-sources.md)

## See also

- [Quant Research](quant-research.md) — trading strategies, backtesting, factor research.
- [MCP wiki: Financial Datasets](../mcp/financialdatasets-ai.md) — first populated MCP record in the wiki.
- [`docs/reference/llm-wiki-pattern.md`](../../reference/llm-wiki-pattern.md) — Karpathy's pattern for personal knowledge bases (relevant when curating provider-specific notes).
