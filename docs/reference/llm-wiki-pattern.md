# Karpathy's LLM Wiki pattern

A reference summary of the **personal knowledge base maintained by an LLM**
pattern, as articulated by Andrej Karpathy in late 2025. This page is
documentation, not a skill — it captures the idea so we can decide later
whether to vendor an existing implementation (e.g. `obsidian-second-brain`)
or author a local skill of our own.

## Sources

- [`gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
  — the long-form "LLM Wiki" pattern document, written to be copy-pasted
  into your own LLM agent so it can co-design the specifics with you.
- [`x.com/karpathy/status/2039805659525644595`](https://x.com/karpathy/status/2039805659525644595)
  — the original announcement tweet ("LLM Knowledge Bases"), which is
  the ~1-page version of the gist and the seed of the broader pattern.

## TL;DR

The wiki is a **persistent, compounding artifact**. RAG re-derives knowledge
from raw sources on every query; an LLM Wiki *compiles* that knowledge once
into structured markdown and *keeps it current* as new sources arrive.

> Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.
> — Karpathy, [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## The original tweet (verbatim)

> **LLM Knowledge Bases**
>
> Something I'm finding very useful recently: using LLMs to build personal
> knowledge bases for various topics of research interest. In this way, a
> large fraction of my recent token throughput is going less into
> manipulating code, and more into manipulating knowledge (stored as
> markdown and images). The latest LLMs are quite good at it. So:
>
> **Data ingest:** I index source documents (articles, papers, repos,
> datasets, images, etc.) into a `raw/` directory, then I use an LLM to
> incrementally "compile" a wiki, which is just a collection of `.md` files
> in a directory structure. The wiki includes summaries of all the data in
> `raw/`, backlinks, and then it categorizes data into concepts, writes
> articles for them, and links them all. To convert web articles into `.md`
> files I like to use the Obsidian Web Clipper extension, and then I also
> use a hotkey to download all the related images to local so that my LLM
> can easily reference them.
>
> **IDE:** I use Obsidian as the IDE "frontend" where I can view the raw
> data, the compiled wiki, and the derived visualizations. Important to
> note that the LLM writes and maintains all of the data of the wiki, I
> rarely touch it directly. I've played with a few Obsidian plugins to
> render and view data in other ways (e.g. Marp for slides).
>
> **Q&A:** Where things get interesting is that once your wiki is big
> enough (e.g. mine on some recent research is ~100 articles and ~400K
> words), you can ask your LLM agent all kinds of complex questions
> against the wiki, and it will go off, research the answers, etc. I
> thought I had to reach for fancy RAG, but the LLM has been pretty good
> about auto-maintaining index files and brief summaries of all the
> documents and it reads all the important related data fairly easily at
> this ~small scale.
>
> **Output:** Instead of getting answers in text/terminal, I like to have
> it render markdown files for me, or slide shows (Marp format), or
> matplotlib images, all of which I then view again in Obsidian. You can
> imagine many other visual output formats depending on the query. Often,
> I end up "filing" the outputs back into the wiki to enhance it for
> further queries. So my own explorations and queries always "add up" in
> the knowledge base.
>
> **Linting:** I've run some LLM "health checks" over the wiki to e.g.
> find inconsistent data, impute missing data (with web searchers), find
> interesting connections for new article candidates, etc., to
> incrementally clean up the wiki and enhance its overall data integrity.
> The LLMs are quite good at suggesting further questions to ask and look
> into.
>
> **Extra tools:** I find myself developing additional tools to process
> the data, e.g. I vibe coded a small and naive search engine over the
> wiki, which I both use directly (in a web ui), but more often I want to
> hand it off to an LLM via CLI as a tool for larger queries.
>
> **Further explorations:** As the repo grows, the natural desire is to
> also think about synthetic data generation + finetuning to have your LLM
> "know" the data in its weights instead of just context windows.
>
> **TL;DR:** raw data from a given number of sources is collected, then
> compiled by an LLM into a `.md` wiki, then operated on by various CLIs
> by the LLM to do Q&A and to incrementally enhance the wiki, and all of
> it viewable in Obsidian. You rarely ever write or edit the wiki
> manually, it's the domain of the LLM. I think there is room here for an
> incredible new product instead of a hacky collection of scripts.

## Architecture

Three layers, from the gist:

1. **Raw sources** — your curated source documents (articles, papers,
   images, datasets). **Immutable** — the LLM reads but never modifies
   them. This is your source of truth.
2. **The wiki** — a directory of LLM-generated markdown (summaries,
   entity pages, concept pages, comparisons, an overview, a synthesis).
   The LLM owns this layer entirely; you read it, the LLM writes it.
3. **The schema** — a `CLAUDE.md` / `AGENTS.md` that tells the LLM how
   the wiki is structured, what the conventions are, and what workflows
   to follow. You and the LLM co-evolve this over time.

## Operations

| Operation | What it does |
| --------- | ------------ |
| **Ingest** | Drop a new source into `raw/`. The LLM reads it, summarizes, files it under the right entity/concept pages, updates the index, appends to the log. A single source might touch 10–15 pages. |
| **Query** | Ask a question. The LLM reads the index, drills into relevant pages, and answers — as markdown, a comparison table, a Marp deck, a matplotlib chart. **File the good answers back into the wiki** so explorations compound. |
| **Lint** | Periodic health check. Find contradictions, stale claims, orphan pages, missing cross-references, data gaps. Suggests new questions to investigate and new sources to look for. |

## Two special files

- **`index.md`** — content-oriented catalog. Every page listed with a link
  and one-line summary, organized by category. The LLM updates it on every
  ingest and reads it first when answering a query. At ~100 sources / a few
  hundred pages this works without embedding-based RAG.
- **`log.md`** — chronological, append-only. Use a consistent prefix
  (e.g. `## [2026-04-02] ingest | Article Title`) so the log becomes
  greppable: `grep "^## \[" log.md | tail -5`.

## Why this works

Maintenance — not reading or thinking — is what kills personal wikis.
Updating cross-references, keeping summaries current, noting contradictions
across dozens of pages: humans give up because the burden grows faster than
the value. LLMs don't get bored, don't forget a back-link, and can touch
15 files in one pass. The wiki stays maintained because the cost of
maintenance is near zero.

The pattern is, in spirit, Vannevar Bush's [Memex](https://en.wikipedia.org/wiki/Memex)
(1945) — a private, curated knowledge store with associative trails. The
part Bush couldn't solve was *who does the maintenance*. The LLM does.

## Ecosystem

Implementations and adjacent tools that have grown around this pattern:

- **[`eugeniughelbur/obsidian-second-brain`](https://github.com/eugeniughelbur/obsidian-second-brain)**
  — a Claude Code skill (not an Obsidian plugin) that pushes the pattern
  further: 31 slash commands + scheduled agents + Python scripts. Adds
  AI-first conventions (machine-readable preambles, bi-temporal facts,
  a "Two-Output Rule" where every answer also updates relevant pages),
  vault-first research that scans existing notes before going to the
  web, and `_CLAUDE.md` / `index.md` / `log.md` / `SOUL.md` /
  `CRITICAL_FACTS.md` (≈120 tokens always loaded) at the vault root.
  *"If Karpathy's wiki is a knowledge base you maintain with an LLM,
  this is a knowledge base that maintains itself."*
- **[`tobi/qmd`](https://github.com/tobi/qmd)** — local search engine for
  markdown (hybrid BM25 + vector + LLM re-ranking, on-device). Has both a
  CLI for the LLM to shell out to and an MCP server. Mentioned by the
  gist as the natural upgrade path once the index file alone stops
  scaling.
- **Obsidian Web Clipper**, **Marp** (markdown-to-slides), **Dataview**
  (frontmatter queries) — the supporting tools the gist recommends.

## Relation to this repo

This repo's [`project-knowledge-harness`](../skills/project-knowledge-harness.md)
is **task memory** — `TODO.md` + `backlog/` + `pitfalls/`, oriented around
shipped/deferred work and past traps. Karpathy's LLM Wiki is **knowledge
memory** — a curated, synthesized view of an external research area. The
two are orthogonal and could coexist on the same project.

Possible follow-ups (not committed):

- Vendor `obsidian-second-brain` into `skills/vendor/` (license permitting),
  alongside `project-knowledge-harness` as a "two flavors of memory" pair.
- Author a minimal local `llm-wiki-bootstrap` skill — just the gist's
  three-layer architecture + `index.md` / `log.md` + `ingest` / `query` /
  `lint` commands, no Obsidian dependency.

If you want to track either, add a `P3` entry via
[`scripts/add-todo.sh`](scripts.md).
