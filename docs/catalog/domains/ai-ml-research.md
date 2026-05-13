# AI/ML Research

Experiment tracking, model lifecycle, data versioning, notebooks, fine-tuning,
agent frameworks, and the broader research-engineering tooling stack.

## Skills in this repo

### Local

| Skill | One-line | Notes |
|---|---|---|
| [`mlflow-tracking`](../../skills/mlflow-tracking.md) | Generic MLflow — sqlite + `mlflow ui` solo, PostgreSQL + MinIO docker for teams; LLM tracing, registry, autolog. | |
| [`dvc-ml-workflow`](../../skills/dvc-ml-workflow.md) | DVC pipelines + queued experiments with metrics auto-bound to ephemeral commits. | |
| [`marimo-batch-mlflow`](../../skills/marimo-batch-mlflow.md) | marimo dual-mode (UI + batch CLI) notebooks with Tyro + MLflow. | |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| [`marimo-notebook`](../../skills/marimo-notebook.md) | [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook) | flat |
| [`streamlit-to-marimo`](../../skills/streamlit-to-marimo.md) | [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/main/skills/streamlit-to-marimo) | flat |
| [`anywidget`](../../skills/anywidget.md) | [`marimo-team/skills`](https://github.com/marimo-team/skills/tree/main/skills/anywidget) | flat |
| [`deep-research`](https://github.com/199-biotechnologies/deep-research) | `199-biotechnologies/deep-research` | `deep-research` series |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| `AI-research-SKILLs` (full library) | [`Orchestra-Research/AI-research-SKILLs`](https://github.com/Orchestra-Research/AI-research-SKILLs) | `wishlist` | 98 skills across 23 categories — full lifecycle from architecture (LitGPT, Mamba, NanoGPT) through fine-tuning (Axolotl, LLaMA-Factory, PEFT) to inference (vLLM, TensorRT-LLM). Too broad to vendor wholesale; will likely cherry-pick. | `npx @orchestra-research/ai-research-skills` (their npm wrapper) or browse and `npx skills@latest add Orchestra-Research/AI-research-SKILLs/<category>/<skill>`. |
| `bio-research` plugin | [`anthropics/knowledge-work-plugins/bio-research`](https://github.com/anthropics/knowledge-work-plugins/tree/main/bio-research) | `wishlist` | PubMed, BioRender, bioRxiv, ChEMBL, Benchling, Open Targets connectors. Not directly applicable but useful as a reference for life-sciences research workflows. | `claude plugin install bio-research@knowledge-work-plugins` |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| _none surveyed yet_ | | | | |

## Backlog (TODO `P?` items)

See the [`P?` lane in `TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md):

- `[?/L]` **LangChain / LangSmith / LangServe / LangGraph / Langfuse** — group orchestration + observability stack into one coherent skill set.
- `[?/L]` **LLM fine-tuning skill** — practical workflow for supervised fine-tuning and adapter-based tuning.
- `[?/M]` **Build MCP skill** — minimum workflow for creating, testing, and documenting MCP servers (note: `mcp-builder` is already vendored — re-evaluate if this still needed).
- `[?/M]` **Hugging Face Spaces + Gradio skill** — demo app deployment, secrets, local-to-hosted handoff.
- `[?/M]` **Data visualization skill** — Matplotlib + Seaborn + Plotly for exploratory + report-ready output.

## See also

- [`docs/reference/deep-research-landscape.md`](../../reference/deep-research-landscape.md) — survey of deep-research tooling and personas.
- [`docs/reference/llm-wiki-pattern.md`](../../reference/llm-wiki-pattern.md) — Karpathy's LLM Wiki pattern for personal research notes.
- [Quant Research](quant-research.md) — overlap on experiment-tracking + notebook stack.
