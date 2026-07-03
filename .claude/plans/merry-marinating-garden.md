# Plan: Make `clash-proxy-api` a genuinely useful, multi-client Clash/mihomo control skill

## Context

`skills/local/clash-proxy-api/` was bootstrapped by Codex. It works but is narrow and
machine-specific: it only wraps the controller API for `status/groups/proxies/delay/switch/egress`,
hardcodes one host's assumptions (`/home/taa/...` path, `127.0.0.1:9090` + port `7890`, node names
`Hanru`/`David`, group `PROXY`), has no `## Gotchas` / `## Available scripts` sections, promises
"reload config" it never implements, and lets `egress` traceback on network errors.

The goal is a skill you can talk to naturally — *"what's my current node?"*, *"switch to the JP node"*,
*"am I in global or rule mode?"*, *"turn on TUN"*, *"reload my config"*, *"the API isn't working, how do I
turn it on?"*, *"there's no system-proxy toggle on my Ubuntu box"* — that **adapts to the OS and client**.

Research corrected two load-bearing assumptions:
- **The controller is not always `127.0.0.1:9090`.** Clash Verge Rev defaults to `127.0.0.1:9097`
  (proxy ports `7897/7898`). The skill must *discover* the controller, never hardcode it.
- **Clash for Windows is dead** (repo deleted ~late 2023). Current landscape: **mihomo core/CLI**,
  **Clash Verge Rev** (GUI, mainstream CFW replacement), **ClashX / ClashX Meta** (macOS), plus
  mihomo-party / FlClash. `PATCH /configs` *can* set `mode`/`tun`/`allow-lan` at runtime, but enabling
  TUN usually needs a core `/restart` **and** elevated privileges (Service Mode).

### Assumed scope (user stepped away during clarification — adjust at approval)
1. **Control scope:** API control **plus** OS system-proxy toggling (macOS `networksetup` / GNOME
   `gsettings`), guarded by `--dry-run`/confirm — this is the explicit "Ubuntu has no toggle" gap.
   Mixin/config-file edits stay as *guidance*, not automation.
2. **First-class clients:** mihomo core/CLI, Clash Verge Rev, ClashX/ClashX Meta; remote/router/Docker
   via `CLASH_CONTROLLER`/`CLASH_SECRET` env.
3. **Repo wiring:** full integration (marketplace + docs + README).

## Design principles

- **Self-contained + portable.** `clash_api.py` stays `#!/usr/bin/env python3`, **stdlib-only** (no `uv`
  dependency for the core — `python3` is far likelier present downstream). Optional `import yaml` if
  available; otherwise a light regex scan for the two top-level keys we need.
- **Discover, never hardcode.** Reuse the proven discovery contract from the user's TV helper
  `~/.local/share/chezmoi/dot_config/television/executable_clash-parse.py` (`cmd_controller`,
  `_runtime_candidate_paths`, `_active_profile_path`, the `$CLASH_CONFIG` set-but-missing-is-an-error
  rule) by **porting** that logic into the skill's own script.
- Structured summary to **stdout**, diagnostics to **stderr**, `--help` with examples + exit codes,
  `--dry-run` on every mutating op. Bash scripts target **bash 3.2**.

## Files to change / add

### 1. Rewrite `scripts/clash_api.py` (stdlib-only, portable)

**Controller discovery** (replace `resolve_controller`, keep it as the reliable core):
1. `--controller` (+ `--secret` — fix current bug where `--secret` is ignored unless `--controller` is set).
2. `CLASH_CONTROLLER` / `CLASH_SECRET` env.
3. Optional TV hook: `~/.config/television/clash-source.sh controller` (keep as bonus, guarded).
4. **Local config parse** (ported from `clash-parse.py`): `$CLASH_CONFIG` (error, no fallback, if set-but-missing)
   → `~/.config/clash/profiles/list.yml` active profile → `~/.config/{clash,mihomo}/config.{yaml,yml}`
   → macOS `~/Library/Application Support/{clash,mihomo, clash-verge-rev app dirs}/…`. Prefer the runtime
   `config.yaml` over subscription profiles (they usually omit `external-controller`/`secret`). Read
   `external-controller` + `secret` via optional PyYAML or a regex scan of those top-level keys.
5. Probe common defaults in order: `127.0.0.1:9090`, then `127.0.0.1:9097` (Verge Rev), via `GET /version`.
6. All fail → structured error (exit `3`) listing what was tried, pointing at `doctor` + the enable-API reference.

**Subcommands** (extend; drop hardcoded `preferred` group list and Hanru/David/PROXY specifics):
- `status` — controller, secret yes/no, version (+ meta/premium), **mode + tun + ports from `GET /configs`**, then generic selector-group list (`GLOBAL` last, else alpha).
- `config get` — `GET /configs`.
- `mode <rule|global|direct>` — `PATCH /configs {"mode":…}`.
- `tun <on|off> [--restart]` — `PATCH /configs {"tun":{"enable":…}}`; warn re: privileges/Service Mode; `--restart` → `POST /restart`.
- `allow-lan <on|off>` — `PATCH /configs`.
- `reload [--path P] [--dry-run]` — `PUT /configs?force=true {"path":…}` (implements the long-promised reload).
- `connections [--json]` / `connections close [--id X | --all --yes]` — `GET`/`DELETE /connections[/:id]`.
- `rules [--filter]` — `GET /rules`.
- `groups [--members]`, `proxies [--filter]` — keep.
- `delay <proxy>` — keep; parse+print delay clearly. `group-delay <group>` — `GET /group/:name/delay` (mihomo, test all members).
- `switch <group> <proxy>` — keep validation (group selectable + proxy is a member).
- `egress` — **fix**: wrap network errors as `ClashError` (exit `3`); default proxy derived from discovered `mixed-port`/`port` (fallback `7890`).
- `doctor` — probe discovery, report what was found/tried, detect OS + likely client (scan config dirs / running procs), and on failure point to the exact client's steps in the enable-API reference. Powers *"turn the API on for me."*
- Global: `--json` opt-in on query cmds; `--help` epilog with **exit codes** (`0` ok, `1` usage, `2` group/proxy not found, `3` controller unreachable, `4` op rejected).

### 2. Add `scripts/clash_sysproxy.sh` (bash 3.2) — OS system-proxy toggle
`detect` | `on <host:port>` | `off`, `--dry-run` (real preview) + confirm/`--yes`:
- macOS: `networksetup -set{web,securewebproxy,socksfirewall}proxy` / `-setwebproxystate off` on the active service (resolved via `-listnetworkserviceorder`).
- GNOME/Ubuntu: `gsettings set org.gnome.system.proxy mode 'manual'|'none'` + host/port keys.
- Always also print `export http_proxy/https_proxy/all_proxy` lines (can't mutate parent shell).
- No `networksetup`/`gsettings` → print env-var approach + reference pointer. `--help`, exit codes, prose→stderr.

### 3. Add `references/` (loaded on demand)
- `references/enable-api-by-client.md` — the research deliverable. Per **client × OS**: how to turn on
  `external-controller`, its default address/port/secret, and where **System Proxy / TUN / Service Mode /
  Mixin** live. Covers mihomo core/CLI, Clash Verge Rev (`:9097`, Service Mode for TUN, Merge/Extend for
  Mixin), ClashX/ClashX Meta, mihomo-party/FlClash (pointers), legacy CFW (discontinued → migrate), and
  remote/OpenClash/Docker (`CLASH_CONTROLLER` env). *Verify current details against the mihomo wiki +
  Clash Verge Rev repo during implementation.*
- `references/api-endpoints.md` — full endpoint catalog (methods/payloads) incl. the streaming ones the
  script doesn't wrap (`/traffic`, `/logs`, `/memory`), `POST /restart`, `/providers/proxies` healthcheck.

### 4. Rewrite `SKILL.md` (< 500 lines, pueue-job-queue structure)
Pushy 120–500-char description with **no** hardcoded `9090`/`7890`/node names; emphasize discovery,
multi-client, enable-API guidance, mode/TUN/system-proxy control. Sections: When to use / When NOT →
**Mental model** (3 layers: API control / enable-when-off / OS-client toggles the API can't do; "never
hardcode, always discover") → Quick start (`doctor` first; discovery-based invocation, no absolute home
path) → **Intent → command map** (the conversational core) → Workflows (switch node; enable API from
scratch; enable TUN; toggle system proxy on Linux — literal command + expected-output blocks) →
**Available scripts** (per-subcommand flags + exit codes) → **Reference files** (with "Read when …" load
conditions) → **Gotchas** (controller≠9090; port≠7890 derive from `/configs`; TUN-via-API needs
privileges+restart; URL-test groups reselect; never print `secret`; prefer runtime config over
subscription profile; System Proxy is OS-level not an API concept; Mixin is config-file not runtime;
switching a group reroutes all proxied traffic; `$CLASH_CONFIG` set-but-missing is a hard error by design).
Refresh `agents/openai.yaml` short description to the broader scope.

### 5. Repo integration (per CLAUDE.md)
- `skills/.claude-plugin/marketplace.json` — add `./local/clash-proxy-api` to the **infra-and-docs** group
  (+ tags `clash`, `mihomo`, `proxy`); run `make marketplace`.
- `docs/skills/clash-proxy-api.md` (match existing skills-page convention/bilingual pattern), a row in
  `docs/skills/index.md`, a nav entry in `mkdocs.yml`, a row in `README.md` "What's in here".
- **No discovery symlinks** — downstream-only skill, not exercised in-repo (verify none exist under
  `.claude/skills/` / `.agents/skills/`; do not add).

## Verification

1. `bash skills/local/skill-author/scripts/lint-skill.sh skills/local/clash-proxy-api` → clean.
2. `python3 scripts/clash_api.py --help` and each subcommand `--help` render usage + exit codes.
3. **Reachable-controller path** (local controller running): `doctor`, `status`, `groups --members`,
   `delay <node>`, `mode rule`, `tun on --dry-run` (or a real toggle if elevated), `reload --dry-run`,
   `connections`, `egress`. Confirm discovery finds the real address (esp. a `:9097` Verge box) without env vars.
4. **Unreachable path** (stop controller / unset env): `doctor` emits OS+client-specific enable guidance and exits `3`.
5. `bash scripts/clash_sysproxy.sh detect`, `on 127.0.0.1:7890 --dry-run`, `off --dry-run` on macOS and a GNOME box.
6. `make marketplace`; `make docs-build` (optional); if `TODO.md` touched, `./scripts/todo-kanban.sh --validate-only`.
