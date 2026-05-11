# Deep Research landscape

This page surveys the **commercial Deep Research products** from major AI
vendors and the **open-source skills/frameworks** that try to reproduce
similar capability locally. It also explains what this repo vendors
(`deep-research/`) and which adjacent options are deliberately *not*
vendored.

## Commercial Deep Research products (2024–2026)

The five major vendors converged on a similar shape — multi-agent
planning, parallel retrieval, citation-grounded synthesis — but with
different defaults around browser scope, model size, and pricing.

| Vendor | Product | Launched | Architecture | Notable |
|---|---|---|---|---|
| **OpenAI** | ChatGPT Deep Research (`o3-deep-research`, `o4-mini-deep-research`) | 2025-02 | Plan → multi-step search → cited report | Plus 25/mo, Pro 250/mo; 2026-02 added scoped sites + collaborative planning + live progress |
| **Google** | Gemini Deep Research (Interactions API) | 2024-12 | Lead agent + parallel sub-agents + synthesis agent | Hooks into Gmail/Drive/Chat; 1M-token context; Canvas visualizations; 2026-04 added MCP tool connectors |
| **xAI** | Grok DeepSearch / DeeperSearch / Grok 4 Heavy | 2024-Q2 → 2025-07 | Multi-agent parallel reasoning, live X + web search | 256k token context; no formal citations yet; emphasizes raw performance |
| **Anthropic** | Claude Research | 2025-06 (eng blog) | LeadResearcher + sub-agents + CitationAgent | ~90% accuracy uplift over single-agent (Opus 4 lead + Sonnet 4 sub); strict enterprise privacy |
| **Meta** | (no first-party DR product) | — | — | LLaMA 4 Scout/Maverick are multimodal foundation models; deep-research must be assembled from LangChain / LlamaIndex / vector DBs |

The shared pattern across all four shipping products:

1. **Plan** — decompose query into sub-questions
2. **Parallel retrieve** — spawn sub-agents that hit web search / docs / files
3. **Iterate** — re-plan based on what's found, follow citations
4. **Synthesize** — assemble a cited report (markdown / HTML / PDF)

Typical wall time is 2–20 minutes; cost is gated by subscription tier or
per-call API metering.

## Reproducing Deep Research locally — the six layers

A real "deep research" stack for an agent CLI is **not a single skill**.
Decompose it into six layers; pick a tool per layer:

| Layer | What it does | Representative tools |
|---|---|---|
| 1. **Planning / decomposition** | Turn the question into sub-questions, evidence requirements, and a research plan | `199-biotechnologies/claude-deep-research-skill` (vendored), `langchain-ai/deepagents` (Python framework, *not* a skill) |
| 2. **Retrieval** | Web / news / GitHub / PDF search | [`tavily-ai/skills/tavily-search`](https://github.com/tavily-ai/skills), [`firecrawl/cli/skills/firecrawl-search`](https://github.com/firecrawl/cli) |
| 3. **Extraction** | Pull main content, tables, multi-page text out of fetched URLs | `firecrawl-scrape`, `firecrawl-crawl`, `firecrawl-parse` |
| 4. **Browser interaction** | Login walls, JS rendering, dynamic UIs, downloads | [`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser) (32k⭐), [`browser-use/browser-use`](https://github.com/browser-use/browser-use) (93k⭐) |
| 5. **Evidence management** | Source registry, claim ledger, citation verification | `199-biotechnologies/claude-deep-research-skill` (built-in) |
| 6. **Synthesis** | Final report (markdown / HTML / PDF) with inline citations | `199-biotechnologies/claude-deep-research-skill`, `tavily-ai/skills/tavily-research` |

The 2-skill minimum that gets you something usable: **(1) + (5) + (6)**
from one disciplined research-flow skill, plus **(2)** from a search
backend you trust.

## What this repo vendors

Just **one** skill, deliberately:

- **`vendor/deep-research/deep-research`** — from
  [`199-biotechnologies/claude-deep-research-skill`](https://github.com/199-biotechnologies/claude-deep-research-skill)
  (646⭐). A pure prompt-flow skill covering planning, evidence
  management, and synthesis. Four modes: `quick` (3 phases, 2–5 min),
  `standard` (6 phases, 5–10 min, default), `deep` (8 phases,
  10–20 min), `ultradeep` (8+ phases, 20–45 min). Uses an evidence
  ledger + claim ledger so each finding traces back to its source.

**Why only one?** Deep-research stacks built from
[`tavily-ai/skills`](https://github.com/tavily-ai/skills),
[`firecrawl/cli`](https://github.com/firecrawl/cli),
[`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser),
or [`browser-use/browser-use`](https://github.com/browser-use/browser-use)
all introduce **paid API keys, hosted backends, or cloud browser
sessions**. Keeping this repo cost-free by default means anyone can run
the vendored research skill against whatever search/browser tools their
agent already has (`WebSearch`, `WebFetch`, MCP, etc.) without signing
up for a third-party service.

If you want a higher-fidelity pipeline, install those skills *alongside*
this one — they compose cleanly.

## Adjacent options *not* vendored — and why

Recorded so future agents don't relitigate it:

| Option | Stars | Why not vendored |
|---|---:|---|
| [`tavily-ai/skills`](https://github.com/tavily-ai/skills) | 285⭐ | Requires Tavily account / API key. Excellent if you're willing to pay; install separately when you are. |
| [`firecrawl/cli`](https://github.com/firecrawl/cli) | 375⭐ | 9 skills (search/scrape/crawl/map/extract/agent…). Free tier exists but production use needs a key. Better as a per-project install. |
| [`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser) | 32k⭐ | Browser automation is a heavy dependency (Chromium, profiles). Out of scope for a research-only stack; install if you actually need it. |
| [`browser-use/browser-use`](https://github.com/browser-use/browser-use) | 93k⭐ | Skills.sh shows a failed Gen Agent Trust Hub security audit. Skip until that resolves. |
| [`langchain-ai/deepagents`](https://github.com/langchain-ai/deepagents) | 22k⭐ | **Not a `SKILL.md` repo** — it's a Python package / framework. Cannot be vendored as an agent skill. ChatGPT-style summaries sometimes mislabel it. |
| [`24601/agent-deep-research`](https://github.com/24601/agent-deep-research) | 4⭐ | Genuine Gemini Interactions API wrapper, but too small / experimental to commit to. Worth re-evaluating later. |

### Things that *look* like deep-research skills but aren't

- [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills)
  (124k⭐) — name and star count are misleading. It's **a single
  `CLAUDE.md`** distilling four Karpathy observations on LLM coding
  pitfalls. Not a skill, not about research. See
  [Karpathy's LLM Wiki pattern](llm-wiki-pattern.md) for the
  *separate* knowledge-base pattern Karpathy actually published in his
  [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## See also

- [Karpathy's LLM Wiki pattern](llm-wiki-pattern.md) — the persistent
  knowledge-base pattern that complements deep research (research
  produces reports; the wiki accumulates them)
- [SDD frameworks & agent harnesses](sdd-and-harnesses.md) — same
  layering distinction (skill / framework / harness) applied to
  spec-driven development
- [Skill risk evaluations](skills-risk-evaluations.md) — how to decide
  whether a workflow should become a skill at all
