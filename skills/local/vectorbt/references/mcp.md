# Optional official PRO MCP

Read this only for MCP setup/repair or when the user chooses MCP. Sources:

- VBT: https://members.vectorbt.pro/using-ai/
- Codex: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- Claude Code: https://code.claude.com/docs/en/mcp

Recheck current client help/docs when configuration behavior differs. No custom
MCP search engine is shipped. `vbt_mcp.py serve` sets version-aligned asset paths
and launches the installed `vectorbtpro.mcp_server.serve(transport="stdio")`.

## Prepare the target environment

Identify the project Python first. Follow its package manager/lockfile to install
the selected PRO release and its official MCP/knowledge extras when needed.
Consult that release's `pyproject.toml`: extras and MCP major versions change.
For example, PRO 2026.9.5 declares `mcp>=2,<3`; copying an old FastMCP/mcp-v1
recipe into it is not reliable. Do not install into system Python.

Using the same cache override for every command, if one was selected:

```bash
python3 scripts/vbt_context.py sync-pro --python /project/.venv/bin/python --messages
/project/.venv/bin/python scripts/vbt_mcp.py check
# Allow more time for the first cold BM25 index build:
/project/.venv/bin/python scripts/vbt_mcp.py check --timeout 900
```

The initial BM25 build can take longer than subsequent calls. A dependency error
is not a credential error. The sync needs gh authentication, but the server's
three preloaded local assets need no token in client configuration. Embeddings
or other new downloads may require separate provider/asset setup; don't enable
them for this initial connection test.

Native document/BM25 indexes also live under the selected XDG cache, in a runtime
directory keyed by the asset generation. Refreshing assets cannot accidentally
reuse an index from an earlier snapshot of the same tag.

## Configure the requested client

The helper previews by default and writes only when invoked with `--apply` in an
authorized setup task. It uses project scope and preserves unrelated values.

```bash
python3 scripts/vbt_mcp.py config --client codex \
  --project /project --python /project/.venv/bin/python
# Apply the reviewed entry during the requested setup:
python3 scripts/vbt_mcp.py config --client codex \
  --project /project --python /project/.venv/bin/python --apply

python3 scripts/vbt_mcp.py config --client claude \
  --project /project --python /project/.venv/bin/python --apply
```

Codex uses `/project/.codex/config.toml`; Claude Code uses `/project/.mcp.json`.
Config contains absolute interpreter/helper/cache paths, not credentials. It is
host-specific: inspect it before sharing across machines. No global configuration
is changed. If the user requested another scope, use the client's supported
native configuration flow rather than pretending this helper supports it.
If a skill installation moves, reconcile the stored absolute helper path too.

An identical entry is a no-op. A differing existing `vectorbtpro` entry is not
overwritten by the helper. Inspect that entry and use the agent's editor to
reconcile only the requested server, preserving other settings and secrets;
then parse the complete file and verify it with the native client.

## Verify each layer

1. `/project/.venv/bin/python scripts/vbt_mcp.py check` starts an actual stdio
   client and checks tool discovery, environment, page reading and BM25 search.
   It reports **server_verified**, never **client_loaded**.
2. In the project, run `codex mcp get vectorbtpro` or
   `claude mcp get vectorbtpro` to check native configuration loading. Avoid
   displaying secret-bearing unrelated configurations.
   Codex ignores untrusted project configuration: a missing entry here does not
   by itself mean the TOML is invalid. Check the actual project's trust state.
   Claude can recognize `.mcp.json` while reporting pending client approval.
3. Reload the client if needed and invoke `get_environment` and `get_page` through
   its connected tools. Project trust and MCP permission UI belong to the client;
   don't claim the client is connected before an actual call succeeds.

For normal queries use object/page lookup and explicit `search_method="bm25"`
when appropriate. Native search defaults are unchanged. Official `run_code` uses
a persistent kernel; use it for exploration and validate saved project code in
a fresh process before reporting reproducible results.

After refreshing assets, restart the MCP server to adopt the new generation;
existing readers deliberately retain their original consistent snapshot. The
launcher refuses a missing/corrupt/wrong-version three-asset cache and explains
which sync command repairs it.
