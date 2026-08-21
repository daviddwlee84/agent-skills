# Domains

Per-domain hub pages. Each hub is a single-page entry point that pulls
together the local skills, vendored skills, external (manual-install)
skills, MCP servers, and backlog items relevant to a professional
domain.

## Hubs

| Hub | Coverage | Status |
|---|---|---|
| [Finance](finance.md) | Banking, capital markets, equity research, wealth management, fund admin. | Populated |
| [Quant Research](quant-research.md) | Quant trading, factor research, backtesting, live execution. | Populated |
| [AI/ML Research](ai-ml-research.md) | Experiment tracking, model lifecycle, fine-tuning, agent frameworks. | Populated |
| [Web & Fullstack](web-fullstack.md) | Next.js / React / Tailwind / Supabase / Vercel / browser automation / web quality audits. | Populated |
| [Knowledge Work](knowledge-work.md) | Sales / legal / customer support / product / marketing / data / etc. | Mostly template |
| [Agent Harness](agent-harness.md) | SDD frameworks + agent harnesses (the layer above skills), plus reusable control adapters. | Populated |

"Mostly template" / "Template only" hubs are honest about being mostly
empty — they exist so the structure is in place when content arrives.

## How to add a new domain hub

1. Copy [`docs/_snippets/domain-hub-template.md`](https://github.com/daviddwlee84/agent-skills/blob/main/docs/_snippets/domain-hub-template.md) to `docs/catalog/domains/<slug>.md`.
2. Fill in the elevator pitch + the 4 tables (Local / Vendored / External / MCP) — leave `_none yet_` for empty rows.
3. Add the new page to `mkdocs.yml` nav under `Catalog → Domains`.
4. Translate to `docs/catalog/domains/<slug>.zh-TW.md` (every catalog page is bilingual).
5. Cross-link from related hubs (`See also` section) and from any
   relevant reference landscape pages.
6. Run `make docs-build` (strict mode catches missing translations and
   broken links).

For the workflow on adding individual entries to an existing hub
(skills, MCPs, status changes), see
[Adding catalog entries](../../workflows/adding-catalog-entries.md).
