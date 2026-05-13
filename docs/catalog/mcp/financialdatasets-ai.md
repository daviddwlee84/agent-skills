---
name: Financial Datasets MCP
slug: financialdatasets-ai
upstream_url: https://docs.financialdatasets.ai/mcp-server
transport: HTTP
auth: OAuth 2.1 + API key
hosting: Hosted (mcp.financialdatasets.ai)
domain: finance
status: wishlist
license: Proprietary
last_verified: 2026-05-13
---

# Financial Datasets MCP

## TL;DR

Hosted MCP server exposing real-time + historical equities data: pricing,
financial statements, SEC filings, news, insider trades, and screening.
20+ tools accessible from Claude Code / Claude Desktop / Cursor / Managed
Agents via OAuth 2.1 (interactive) or API key (programmatic).

## Tools / capabilities

| Category | Examples |
|---|---|
| Pricing | Current + historical stock prices |
| Financial statements | Income, balance sheet, cash flow, segmented financials |
| Metrics | P/E, market cap, enterprise value, dividend yields |
| Company info | Sector, industry, employee counts |
| SEC filings | 10-K, 10-Q, 8-K + extractable sections (e.g. Risk Factors) |
| Market intelligence | News, insider trades, earnings data |
| Screening | Filter stocks by valuation + financial criteria |
| Specialized | KPI guidance, non-GAAP metrics, central bank rates |

## Auth & install

### Claude Code

```bash
claude mcp add --transport http financial-datasets https://mcp.financialdatasets.ai/
```

OAuth flow runs in the browser on first use.

### Claude Desktop

Settings → Connectors → Add custom connector → paste
`https://mcp.financialdatasets.ai/`. OAuth flow runs in-app.

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "financial-datasets": {
      "url": "https://mcp.financialdatasets.ai/",
      "transport": "http"
    }
  }
}
```

### Managed Agents (programmatic)

Use static bearer vault credentials with the `/api` endpoint
(`X-API-KEY` header). See
[upstream auth docs](https://docs.financialdatasets.ai/mcp-server) for
the API key issuance flow.

## When to use it

- Quick equities lookups during research / writeup workflows.
- Cross-checking SEC filing claims against actual filings.
- Stock screening with valuation criteria.
- Pulling time series for ad-hoc charts.

## When NOT to use it

- Heavy time-series workloads — fetch raw data via the REST API and
  cache locally instead. MCP is per-call.
- Non-equity asset classes (futures, FX, crypto). Coverage is equity-first.
- Backtesting (latency + per-call cost). Use a [Tardis](https://tardis.dev/)
  / vendor SDK + local cache instead.
- Anything requiring deterministic snapshots (the MCP is live data).

## Related skills in this repo

- [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md)
  — local skill that could consume this MCP for factor data.
- [Finance](../domains/finance.md) — domain hub.
- [Quant Research](../domains/quant-research.md) — domain hub.

## Upstream sources

- [Financial Datasets MCP docs](https://docs.financialdatasets.ai/mcp-server) — install + tool reference.
- [Financial Datasets API docs](https://docs.financialdatasets.ai/) — underlying REST API the MCP wraps.
