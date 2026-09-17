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
| [`vectorbt`](../../skills/vectorbt.md) | OSS/PRO library development, release-aligned XDG docs, migration checks, and optional MCP. | `quantitative-finance` group |
| [`nautilus-trader`](../../skills/nautilus-trader.md) | v1 Cython / v2 Rust-PyO3 generation detection, git-tag docs cache, event-driven backtests, sandbox/live-trading gates. | `quantitative-finance` group |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| _none yet_ | | |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| VectorBT Backtesting Skills | [marketcalls/vectorbt-backtesting-skills](https://github.com/marketcalls/vectorbt-backtesting-skills) | `skipped` | Evaluated OSS workflow; OpenAlgo indicator defaults do not match this library-focused skill. | Upstream instructions |
| NautilusTrader docs skill | [aysuio/nt-skill](https://github.com/aysuio/nt-skill) | `skipped` | No license; assumes hosted `latest` docs track the installed release, which fails during the v1 → v2 RC period. | Upstream instructions |
| NautilusTrader skill | [clay584/nautilus-trader-skill](https://github.com/clay584/nautilus-trader-skill) | `skipped` | No license; verified against 1.228.0 and teaches the v1 `TradingNode` API. | Upstream instructions |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| Financial Datasets MCP | [`docs.financialdatasets.ai/mcp-server`](https://docs.financialdatasets.ai/mcp-server) | `wishlist` | OAuth 2.1 + API key | [Per-MCP page](../mcp/financialdatasets-ai.md) |

## Backlog (TODO `P?` items)

See the [`P?` lane in `TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md):

- `[?/L]` **Tardis SDK skill** — historical market data workflows, access assumptions, and example-driven guidance.
- `[?/L]` **Financial data sources skill set** — provider comparison (cross-listed in [Finance](finance.md)).

## See also

- [Finance](finance.md) — banking, capital markets, equity research workflows.
- [AI/ML Research](ai-ml-research.md) — for the experiment tracking + notebook ecosystem (`mlflow-tracking`, `marimo-batch-mlflow`) that quant projects often layer on.
- [`docs/skills/quantatitive-factor-researcher.md`](../../skills/quantatitive-factor-researcher.md), [`vectorbt.md`](../../skills/vectorbt.md), and [`nautilus-trader.md`](../../skills/nautilus-trader.md) — the local skill pages.
