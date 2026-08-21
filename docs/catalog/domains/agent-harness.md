# Agent Harness

Spec-driven development (SDD) frameworks and agent harnesses — the layer
**above** agent skills that owns the requirements → spec → plan → tasks →
execute → verify loop, manages context windows, or runs sub-agents.

This repo focuses on **skills** and intentionally does not ship a SDD
framework or harness. It does ship Herdr's official control adapter: the
runtime is a harness/multiplexer, while the vendored artifact is still a
normal agent skill.

## Skills in this repo

### Local

| Skill | One-line | Notes |
|---|---|---|
| _none — out of scope_ | | We ship skills; harnesses ship the loop that orchestrates skills. Different layer. |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| [`herdr`](../../skills/herdr.md) | [`herdrdev/herdr`](https://github.com/herdrdev/herdr/tree/master/skills/herdr) | flat |

## External skills (manual install)

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | Why this status | Install hint |
|---|---|---|---|---|
| `spec-kit` (skills mode) | [`github/spec-kit`](https://github.com/github/spec-kit) | `evaluated` | The de facto SDD framework (95.5k ⭐). 30+ supported agents. Has a `--skills` install mode that ships its slash commands as agent skills. Documented in [`reference/sdd-and-harnesses.md`](../../reference/sdd-and-harnesses.md). Not vendored — would compete with the per-skill philosophy of this repo. | `uvx --from git+https://github.com/github/spec-kit specify init <project> --integration claude-code --integration-options="--skills"` |
| `get-shit-done` (gsd) | [`gsd-build/get-shit-done`](https://github.com/gsd-build/get-shit-done) | `evaluated` | Earlier, lighter SDD (61.4k ⭐). 6-command loop (`gsd-new-project → gsd-discuss-phase → gsd-plan-phase → gsd-execute-phase → gsd-verify-work → gsd-ship`). | (see upstream README) |
| `gsd-2` | [`gsd-build/gsd-2`](https://github.com/gsd-build/gsd-2) | `evaluated` | Standalone harness (not just a SDD framework). | (see upstream README) |
| OpenClaw | [`openclaw/openclaw`](https://github.com/openclaw/openclaw) | `evaluated` | Standalone CLI/runtime that controls the agent session. Also produces `gstack-openclaw-*` skills (already vendored under `product-planning` series). | (see upstream README) |
| Pi SDK | [`badlogic/pi-mono`](https://github.com/badlogic/pi-mono) | `evaluated` | Agent harness alternative. | (see upstream README) |

## MCP servers

| Name | Upstream | Status | Auth | Records |
|---|---|---|---|---|
| _not applicable_ — harnesses use whatever MCPs the underlying agent has access to | | | | |

## Backlog (TODO `P?` items)

- Harness runtimes remain out of scope; only their reusable skill adapters are eligible for vendoring.

## See also

- [`docs/reference/sdd-and-harnesses.md`](../../reference/sdd-and-harnesses.md) — full survey of SDD frameworks and agent harnesses, with the layering explanation (skill vs SDD framework vs harness).
- `product-planning` series in [`docs/skills/index.md`](../../skills/index.md) — vendored OpenClaw skills (`gstack-openclaw-*`) that *are* in this repo's scope.
- [`herdr`](../../skills/herdr.md) — official control skill, including why binary-emitted installs are preferred for exact version alignment.
