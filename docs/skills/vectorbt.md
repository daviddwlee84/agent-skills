# vectorbt

Develop, debug, optimize and migrate code using **VectorBT OSS or PRO as a Python
library**. This local skill belongs to the `quantitative-finance` marketplace
group with [quantatitive-factor-researcher](quantatitive-factor-researcher.md).

The skill verifies the edition and installed API before using examples. For new
work it prefers PRO when access is confirmed; existing OSS projects keep their
edition unless a feature requirement, measured bottleneck or migration request
warrants a change. Users without PRO access can use public OSS documentation and
their installed package normally.

## What ships

- A short skill entrypoint and on-demand OSS, PRO, migration and MCP references.
- `vbt_context.py doctor`: inspect the project's interpreter, actual imports,
  package versions, PRO repository access and available caches.
- `vbt_context.py sync-pro`: download release assets with the existing GitHub CLI
  login, verify checksums, and generate searchable Markdown with source URLs and
  a page/object index. It also works without installing VBT when given a release.
- `vbt_mcp.py config`, `serve`, `check`: project-scoped Codex/Claude Code setup,
  launch the installed official PRO server, and verify real MCP calls.
- Offline tests using synthetic documents and a fake GitHub CLI; no membership or
  private documentation is needed in CI.

Source: [the local skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/vectorbt).

## Quick start

Commands are relative to the installed skill directory. Pass the strategy
project's Python explicitly if it is not under `.venv`.

```bash
python3 scripts/vbt_context.py doctor --project /path/to/strategy
python3 scripts/vbt_context.py sync-pro --python /path/to/strategy/.venv/bin/python
# Or inspect documentation without installing PRO (choose the desired release):
python3 scripts/vbt_context.py sync-pro --release v2026.9.5
```

Use the returned `index` and `markdown_dir` with `rg`, then read complete relevant
sections and confirm the installed signature. No embeddings or extra LLM API
key is required. Default assets are pages and examples; add `--messages` for
Discord discussions or MCP setup. The example release is not a default pin.

## XDG and freshness

macOS and Linux share the same precedence: `--cache-dir`, then an absolute
`$XDG_CACHE_HOME/vectorbt-agent`, then `~/.cache/vectorbt-agent`. Empty or relative
XDG values fall back to the default. Caches are shared across projects and
isolated by edition/release; downloads and credentials never belong in Git.

Sync checks remote metadata after 24 hours or with `--refresh`. Asset ID,
timestamp, size and digest detect changes even within the same release tag.
Validated generations are selected atomically, leaving active readers on a
consistent old generation. No background scheduler is installed.

`--offline` uses valid local data; a failed metadata request with valid cache
returns an explicit `stale` status. Neither claims the live website is current.
Missing remote digests are reported; invalid checksums or JSON do not replace
the last valid cache. Stop old readers before deleting obsolete cache generations.

## Optional MCP

When requested, prepare the target release's MCP/knowledge dependencies, sync
all three assets, and use the helper to preview/apply the project server entry.
The launcher reuses the same cache and official tools, not a new retrieval
engine. Existing conflicting server entries require a focused merge rather
than being overwritten; unrelated settings are preserved.

`check` verifies the server protocol, environment, document reading and BM25
search. A native client must then load the entry and successfully call a tool;
server validation alone does not establish client connection.

## Validation baseline

Validated on Python 3.12 with OSS 1.1.0 (Plotly 5.24.1) and PRO 2026.9.5
(MCP SDK 2.2.0): fresh-process synthetic backtests, private asset synchronization,
official MCP page/BM25 calls, and isolated native marketplace loading in both
clients. This is a tested baseline, not a universal dependency pin. The OSS
reference records the observed Plotly 7 import incompatibility.

## Sources

- [OSS documentation](https://vectorbt.dev/) and [source](https://github.com/polakowo/vectorbt)
- [PRO AI integration](https://members.vectorbt.pro/using-ai/), [downloads](https://members.vectorbt.pro/downloads/) and [releases](https://github.com/polakowo/vectorbt.pro/releases)
- [XDG specification](https://specifications.freedesktop.org/basedir/latest/)

The official source trees checked during authoring did not ship a skill. The
surveyed third-party skills used different workflow assumptions, including
OpenAlgo-specific indicator defaults; this skill is independently authored.
