# Quant Research

Quantitative trading, factor research, backtesting, and live-execution
workflows. Distinct from the [Finance](finance.md) hub (which covers
banking / capital markets / equity research / fund admin) — overlap is
mostly on the data-source side.

## Skills in this repo

### Local

| Skill | One-line | Notes |
|---|---|---|
| [`quantatitive-factor-researcher`](../../skills/quantatitive-factor-researcher.md) | Python quant-research persona for factor engineering, backtesting, cross-validation, and Sharpe / IR / Tracking Error metrics. | Anchor skill of this hub. |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _none yet_ | | |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| _none surveyed yet — most quant tooling is Python libraries (no agent skill yet)_ | | | | |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| Financial Datasets MCP | [`docs.financialdatasets.ai/mcp-server`](https://docs.financialdatasets.ai/mcp-server) | `wishlist` | OAuth 2.1 + API key | [Per-MCP page](../mcp/financialdatasets-ai.md) |

## Backlog (TODO `P?` items)

See the [`P?` lane in `TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md):

- `[?/M]` **VectorBT skill** — minimum workflow for factor research, backtesting, and result inspection.
- `[?/L]` **VectorBT Pro skill** — assess whether a premium-only skill can reliably point agents at the correct documentation page and paid workflow nuances.
- `[?/M]` **Nautilus Trader skill** — event-driven trading workflows, backtests, and live-trading guardrails.
- `[?/L]` **Tardis SDK skill** — historical market data workflows, access assumptions, and example-driven guidance.
- `[?/L]` **Financial data sources skill set** — provider comparison (cross-listed in [Finance](finance.md)).

## See also

- [Finance](finance.md) — banking, capital markets, equity research workflows.
- [AI/ML Research](ai-ml-research.md) — for the experiment tracking + notebook ecosystem (`mlflow-tracking`, `marimo-batch-mlflow`) that quant projects often layer on.
- [`docs/skills/quantatitive-factor-researcher.md`](../../skills/quantatitive-factor-researcher.md) — the local skill page.
