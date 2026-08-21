# Agent Harness —— Agent 殼層

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

規格驅動開發 (spec-driven development, SDD) 框架與 agent harness ——
位於 agent skill **之上**的層級，負責 requirements → spec → plan →
tasks → execute → verify 這個 loop，或管理 context window、執行
sub-agent。

本 repo 聚焦在 **skill**，刻意 (intentionally) 不 ship SDD framework
或 harness。不過會收錄 Herdr 的官方控制 adapter：runtime 本身是
harness／multiplexer，而 vendored artifact 仍是一般 agent skill。

## 此 repo 內的 skill

### Local

| Skill | 一句話 | 備註 |
|---|---|---|
| _無 —— 不在範圍 (out of scope)_ | | 本 repo ship skill；harness ship 的是「驅動 skill 的 loop」。不同層。 |

### Vendored

| Skill | Upstream | Series |
|---|---|---|
| [`herdr`](../../skills/herdr.md) | [`herdrdev/herdr`](https://github.com/herdrdev/herdr/tree/master/skills/herdr) | flat |

## External skills（手動安裝）

--8<-- "_snippets/external-install.md"

| Skill / Plugin | Upstream | Status | 為何此狀態 | 安裝提示 |
|---|---|---|---|---|
| `spec-kit`（skills mode） | [`github/spec-kit`](https://github.com/github/spec-kit) | `evaluated` | 事實上 (de facto) 的 SDD framework（95.5k ⭐）。支援 30+ agent。有 `--skills` 安裝模式可把 slash command ship 成 agent skill。文件見 [`reference/sdd-and-harnesses.md`](../../reference/sdd-and-harnesses.md)。未 vendor —— 與本 repo 的 per-skill 哲學會競爭。 | `uvx --from git+https://github.com/github/spec-kit specify init <project> --integration claude-code --integration-options="--skills"` |
| `get-shit-done` (gsd) | [`gsd-build/get-shit-done`](https://github.com/gsd-build/get-shit-done) | `evaluated` | 較早、較輕量的 SDD（61.4k ⭐）。六指令 loop（`gsd-new-project → gsd-discuss-phase → gsd-plan-phase → gsd-execute-phase → gsd-verify-work → gsd-ship`）。 | （見 upstream README） |
| `gsd-2` | [`gsd-build/gsd-2`](https://github.com/gsd-build/gsd-2) | `evaluated` | 獨立 harness（不只是 SDD framework）。 | （見 upstream README） |
| OpenClaw | [`openclaw/openclaw`](https://github.com/openclaw/openclaw) | `evaluated` | 控制 agent session 的獨立 CLI / runtime。同時也產出 `gstack-openclaw-*` skill（已歸在 `product-planning` series vendored）。 | （見 upstream README） |
| Pi SDK | [`badlogic/pi-mono`](https://github.com/badlogic/pi-mono) | `evaluated` | Agent harness 的另一選項。 | （見 upstream README） |

## MCP servers

| 名稱 | Upstream | Status | Auth | 紀錄 |
|---|---|---|---|---|
| _不適用 (not applicable)_ —— harness 用底層 agent 能用的 MCP | | | | |

## Backlog（TODO `P?` 條目）

- Harness runtime 仍不在範圍；只有可重用的 skill adapter 才適合 vendor。

## 另見

- [`docs/reference/sdd-and-harnesses.md`](../../reference/sdd-and-harnesses.md)
  —— SDD framework 與 agent harness 的完整 survey，附三層分層
  （skill vs SDD framework vs harness）說明。
- `product-planning` series 在
  [`docs/skills/index.md`](../../skills/index.md) —— vendored 的
  OpenClaw skill（`gstack-openclaw-*`），這些*是*在本 repo 範圍內。
- [`herdr`](../../skills/herdr.md) —— 官方控制 skill，以及為何安裝 binary
  時應優先用 binary-emitted copy 取得精確版本對齊。
