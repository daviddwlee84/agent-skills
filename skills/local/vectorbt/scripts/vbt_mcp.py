#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Configure, serve and check the installed official VectorBT PRO MCP server.

serve/check run under the project Python with its VBT and MCP dependencies.
config is stdlib-only, previews by default, and only writes on --apply.
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib

from vbt_context import ContextError, absolute, cache_root, current_cache, log, release_tag


def load_pro_cache(root: Path):
    # Any incidental library output belongs on stderr, never the MCP stream.
    with redirect_stdout(sys.stderr):
        import vectorbtpro as vbt
    release = release_tag(vbt.version)
    cached = current_cache(root / "pro" / release, {"pages", "examples", "messages"})
    if not cached:
        raise ContextError(f"No valid three-asset cache for {release}. Run vbt_context.py sync-pro --python {sys.executable} --messages with the same --cache-dir.", 2)
    raw = cached[1] / "raw"
    # Native BM25/document indexes must follow XDG too, and must not survive a
    # same-tag asset replacement. Keep them outside immutable raw generations.
    vbt.settings.set("knowledge.cache_dir", root / "pro" / release / "runtime" / cached[0]["generation"])
    for name in ("pages", "examples", "messages"):
        vbt.settings.set(f"knowledge.assets.{name}.assets_dir", raw)
    vbt.settings.set("knowledge.assets.vbt.release_name", release)
    return vbt, cached


def serve(root: Path) -> None:
    vbt, _ = load_pro_cache(root)
    with redirect_stdout(sys.stderr):
        from vectorbtpro.mcp_server import serve as official_serve
    # The official server owns stdout from here. Do not print JSON summaries.
    official_serve(transport="stdio")


def tool_text(name: str, result) -> str:
    text = "\n".join(x.text for x in result.content if getattr(x, "type", None) == "text")
    # MCP SDK 2 uses snake_case attributes; SDK 1 used wire-format camelCase.
    if getattr(result, "is_error", False) or getattr(result, "isError", False) or not text.strip() or text.strip() == "No results found":
        raise ContextError(f"MCP {name} returned an error or no content. Inspect dependencies, release and assets.", 4)
    return text


async def check(root: Path, timeout: float) -> dict:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).absolute()), "serve", "--cache-dir", str(root)])
    async with asyncio.timeout(timeout):
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                required = {"get_environment", "get_page", "search", "get_source"}
                if not required <= names:
                    raise ContextError("Official MCP tool list is incomplete; check the installed VBT/MCP versions.", 4)
                results = {}
                for name, arguments in (
                    ("get_environment", {}),
                    ("get_page", {"url": "/using-ai/", "max_tokens": 1500}),
                    ("search", {"query": "from_signals sl_stop", "asset_names": ["docs"], "search_method": "bm25", "n": 2, "max_tokens": 1500}),
                ):
                    result = await session.call_tool(name, arguments)
                    text = tool_text(name, result)
                    results[name] = {"ok": True, "response_chars": len(text)}
                    if name == "get_environment":
                        environment = json.loads(text)
                        with redirect_stdout(sys.stderr):
                            import vectorbtpro as vbt
                        if environment.get("vectorbtpro_version") != vbt.version or absolute(environment.get("python_executable", "")) != absolute(sys.executable):
                            raise ContextError("MCP interpreter or VBT version does not match the check process.", 4)
                        results[name]["environment"] = environment
                return {"status": "server_verified", "client_loaded": False, "tools": sorted(names), "checks": results,
                        "next": "Reload the configured Codex/Claude Code client and verify an actual tool call there."}


def config(project: Path, python: Path, root: Path, client: str, apply: bool) -> dict:
    if not project.is_dir() or not python.is_file():
        raise ContextError("Existing --project directory and --python executable are required.", 2)
    entry = {"command": str(python), "args": [str(Path(__file__).absolute()), "serve", "--cache-dir", str(root)]}
    if client == "codex":
        entry["cwd"] = str(project)
        entry["startup_timeout_sec"] = 60
        entry["tool_timeout_sec"] = 180
        path = project / ".codex/config.toml"
        original = path.read_text() if path.exists() else ""
        try:
            parsed = tomllib.loads(original)
        except ValueError as exc:
            raise ContextError("Existing Codex TOML is invalid; repair it before adding a server.", 2) from exc
        existing = parsed.get("mcp_servers", {}).get("vectorbtpro")
        lines = ["", "[mcp_servers.vectorbtpro]"]
        for key, value in entry.items():
            lines.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
        updated = original.rstrip() + "\n" + "\n".join(lines) + "\n"
        if existing is None:
            try:
                tomllib.loads(updated)
            except ValueError as exc:
                raise ContextError("Cannot append server to this TOML layout; merge the entry with the agent's editor and validate it.", 2) from exc
    else:
        path = project / ".mcp.json"
        original = path.read_text() if path.exists() else "{}"
        try:
            parsed = json.loads(original)
            servers = parsed.setdefault("mcpServers", {})
            if not isinstance(servers, dict):
                raise ValueError("mcpServers must be an object")
        except (ValueError, AttributeError) as exc:
            raise ContextError("Existing Claude MCP JSON is invalid; repair it before adding a server.", 2) from exc
        existing = servers.get("vectorbtpro")
        if existing is None:
            servers["vectorbtpro"] = entry
        updated = json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
    if existing is not None and existing != entry:
        raise ContextError("A different vectorbtpro server already exists. Inspect and reconcile only that entry with the agent's editor; this helper will not overwrite it.", 2)
    status = "unchanged" if existing == entry else "preview"
    if apply and existing is None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".vbt-config-", dir=path.parent)
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(updated)
            if path.exists():
                os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        status = "configured"
    return {"status": status, "client": client, "scope": "project", "path": str(path), "server": entry,
            "client_loaded": False, "next": "Run check under the project Python, then reload the client. Project trust/approval is managed by the client."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog="Exit codes: 0 success, 2 invalid input/missing cache/conflicting config, 3 runtime/external failure, 4 failed verification. serve reserves stdout for MCP; other commands emit JSON.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "check", "config"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--cache-dir", help="Same override as vbt_context.py; otherwise XDG")
        if name == "check":
            cmd.add_argument("--timeout", type=float, default=180)
        if name == "config":
            cmd.add_argument("--client", choices=("codex", "claude"), required=True)
            cmd.add_argument("--project", required=True)
            cmd.add_argument("--python", required=True)
            group = cmd.add_mutually_exclusive_group()
            group.add_argument("--apply", action="store_true", help="Write the project entry; default is preview")
            group.add_argument("--dry-run", action="store_true", help="Explicit preview; never writes")
    args = parser.parse_args(argv)
    try:
        root = cache_root(args.cache_dir)
        if args.command == "serve":
            serve(root)
            return 0
        if args.command == "check":
            result = asyncio.run(check(root, args.timeout))
        else:
            result = config(absolute(args.project), absolute(args.python), root, args.client, args.apply)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ContextError, ImportError, OSError, TimeoutError, ExceptionGroup) as exc:
        if isinstance(exc, ContextError):
            log(str(exc))
        else:
            log(f"MCP operation failed ({type(exc).__name__}). Check the project Python's VBT/MCP/knowledge dependencies and rerun check; client connection is not verified.")
        return getattr(exc, "code", 3)


if __name__ == "__main__":
    raise SystemExit(main())
