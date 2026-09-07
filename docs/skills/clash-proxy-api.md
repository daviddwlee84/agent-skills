# clash-proxy-api

Discover and drive a running **Clash / mihomo** proxy through its
external-controller REST API — from natural-language requests like "what's my
node?", "switch to the JP node", "go global mode", "turn on TUN", "reload my
config", or "the proxy API isn't reachable". Bundled scripts wrap the
controller API and the OS system proxy; references cover enabling the API
per client and the raw endpoint surface.

| Surface | Question it answers |
|---|---|
| `clash_api.py doctor` | "Is the controller reachable, and if not, which client do I enable the API on?" |
| `clash_api.py status` | "What's my current node, mode, TUN state, ports, and groups?" |
| `clash_api.py switch/mode/tun/reload/connections` | "Change the live proxy: pick a node, set rule/global/direct, toggle TUN, reload, close connections." |
| `clash_api.py delay/group-delay/proxies/rules` | "Test latency, list nodes/rules." |
| `clash_sysproxy.sh` | "Toggle the OS system proxy where the client has no toggle (mihomo CLI, headless, Ubuntu)." |
| `references/enable-api-by-client.md` | "How do I turn on the API / find its address on Verge Rev / ClashX / mihomo? Where are System Proxy, TUN, Service Mode, Mixin?" |
| `references/api-endpoints.md` | "What endpoint do I curl for `/traffic`, `/providers`, `/dns/query`…?" |

The skill's whole point is to **not hardcode assumptions**. Controller discovery
tries `--controller`/`--secret` → `CLASH_CONTROLLER`/`CLASH_SECRET` env → an
optional Television hook → local config files → probes `127.0.0.1:9090` then
`:9097` (Clash Verge Rev). First reachable wins. The proxy port is read from live
config, not assumed to be `7890`.

## When the skill triggers

- "What node/mode am I on?" → `status`. "Switch PROXY to the Japan node" → `delay` then `switch`.
- "Go global / rule / direct mode" → `mode`. "Turn TUN on" → `tun on --restart`.
- "Reload my config", "close all connections", "what's my egress IP" → `reload` / `connections` / `egress`.
- "Is the Clash API on? / it's broken" → `doctor`, then the enable-API reference.
- "There's no system-proxy toggle on my Ubuntu box" → `clash_sysproxy.sh`.
- The user mentions Clash, mihomo, Clash Verge (Rev), ClashX, external-controller, `9090`/`9097`, or a node by name.

## When it doesn't

- Hand-editing subscription/rule YAML — the API reloads and toggles, it doesn't author config. Use the policy repository and the client deployment workflow.
- **Mixin / Merge** config — a client-side config-file feature (Clash Verge / CFW), not a runtime API. The skill guides; it doesn't script it.
- Buying/choosing nodes or managing subscriptions.

## Structure

```
skills/local/clash-proxy-api/
├── SKILL.md                        # intent→command map + gotchas
├── scripts/
│   ├── clash_api.py                # stdlib-only Python 3; controller API client
│   └── clash_sysproxy.sh           # bash 3.2; OS system-proxy toggle
├── references/
│   ├── enable-api-by-client.md     # per client×OS: enable API, System Proxy, TUN, Service Mode, Mixin
│   └── api-endpoints.md            # full endpoint catalog + raw curl recipes
└── agents/openai.yaml              # OpenAI-style launcher descriptor
```

## Design highlights

- **`clash_api.py` is stdlib-only** — no `uv`, no pip. It runs anywhere `python3`
  is present, which is the realistic downstream case. PyYAML is used if importable,
  else a small regex scanner reads the two config keys it needs.
- **Every write supports `--dry-run`**; destructive `connections close --all`
  requires `--yes`; secrets are never printed (`status` says `secret: yes/no`).
- **Exit codes branch retry behavior**: `0` ok, `1` usage, `2` group/proxy not
  found (message lists the real members), `3` controller unreachable, `4` op
  rejected. `clash_sysproxy.sh`: `0/1/2/3`.
- **Three-layer model** — controller API (reliable), enable/discover (when the API
  is off), OS/client toggles the API can't do (System Proxy, Service Mode, Mixin).

## Gotchas the skill encodes

- The controller is **not always `127.0.0.1:9090`** (Verge Rev is `9097`; GUIs pick random ports; routers are on the LAN) — always discover.
- The proxy port is **not always `7890`** — derive it from `status` → ports.
- **Enabling TUN via the API needs an elevated core** (Service Mode / root) and usually a `POST /restart`; a bare `PATCH` returns 204 but doesn't route.
- **System Proxy is an OS setting, not an API concept** — use the client toggle or `clash_sysproxy.sh`.
- `group-delay` / `/providers` / `/restart` are **mihomo-only** (404 on classic Premium cores).

## Verification

```bash
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/clash-proxy-api
python3 skills/local/clash-proxy-api/scripts/clash_api.py doctor                     # discover + diagnose
python3 skills/local/clash-proxy-api/scripts/clash_api.py status                     # against a live controller
bash   skills/local/clash-proxy-api/scripts/clash_sysproxy.sh detect                 # read-only OS proxy state
```

Read commands are safe against a live controller; write commands (`switch`, `mode`,
`tun`, `reload`, `connections close`) preview with `--dry-run`.

## Bounded diagnosis and managed routers

Use `--controller https://HOST:PORT --ca-cert PATH --secret-file PATH --read-only`
for an explicit TLS target. Certificate and hostname validation remain enabled;
redirects and environment proxies are disabled for controller requests. An explicit
target never falls back to a local controller. Remote `egress` needs `--proxy`.

`observe DOMAIN --client IP --duration 20` combines filtered connection snapshots
with routing logs. JSON includes core version, timestamps, matched rule, original
chain order, collection warnings and an evidence state. It does not open the site,
prove application success, or reconstruct past traffic; reports are private metadata.

For Nikki on the managed Pi, use the project `just diagnose-site` wrapper, which
also checks client routes and binds the observation to the confirmed profile.
Use device transactions for changes. See the skill's
`references/managed-router-diagnosis.md` and the
[policy knowledge base](https://github.com/daviddwlee84/clash-rules/blob/main/docs/diagnosis.md).

Transport and observation regression tests:

    python3 -m unittest discover -s skills/local/clash-proxy-api/tests -v
