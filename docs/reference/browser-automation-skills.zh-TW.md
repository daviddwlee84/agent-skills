# Browser automation skills 與 MCP — 瀏覽器自動化 skill 與 MCP

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現。**不自創翻譯**——
    若無公認譯名直接保留英文（如 `MCP`、`SDK`、`SKILL.md`、`a11y tree`、
    `daemon`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁比較常見的**瀏覽器自動化 agent skill / MCP server**。瀏覽器自動化
是給 coding agent 最有價值的能力之一，但這幾個工具的設計取捨差很多。
這頁把取捨講清楚，並說明為何本 repo 目前**不**vendor 任何一個。

## 一覽

五個知名選項，目標都差不多——讓 agent 開真瀏覽器跟頁面互動——但形狀差很多：

| 工具 | ⭐ | 形態 | Auth/session | 成本 | Token 友善度 |
|---|---:|---|---|---|---|
| [`microsoft/playwright-cli`](https://github.com/microsoft/playwright-cli) | 10k | CLI + 1 SKILL.md | 本地 Chromium / 你的 profile | 免費、本地 | a11y-tree snapshot + `eN` ref |
| [`vercel-labs/agent-browser`](https://github.com/vercel-labs/agent-browser) | 33k | CLI + 1 SKILL.md | 本地 Chromium、profile、Vercel Sandbox、AWS Bedrock AgentCore cloud | CLI 免費；雲端 Vercel/AWS 按量 | a11y-tree snapshot + 緊湊 `@eN` ref |
| [`browser-use/browser-use`](https://github.com/browser-use/browser-use) | 93k | CLI + 4 SKILL.md (`browser-use`、`cloud`、`open-source`、`remote-browser`) | 本地 + Browser Use Cloud | 開源本地；Cloud SaaS | 持久 daemon (~50 ms/call)；也提供 MCP |
| [`browserbase/stagehand`](https://github.com/browserbase/stagehand) | 23k | TypeScript SDK | Browserbase cloud（或本地 Playwright） | Browserbase 按量 | Code-first（`page.act("click sign in")`）；不是 SKILL.md |
| [Playwright MCP](https://playwright.dev/agent-cli/introduction) | (Playwright 官方) | MCP server | 本地 Chromium | 免費、本地 | a11y tree，但有完整 MCP schema overhead |

> ⭐ 是整個 repo 的 star，不是單個 skill 的品質指標。`browser-use/browser-use`
> 是個大 framework，star 高是 framework 帶起來的，不代表裡面的 SKILL.md
> 一定比別人好。

## 真正該看的設計取捨

照這幾個維度挑，不要照 star 挑：

### 1. CLI vs MCP vs SDK

- **CLI + SKILL.md**——`playwright-cli`、`agent-browser`、`browser-use`
  (CLI 模式)。Agent 用 `playwright-cli click e15` shell 出去。每個指令
  就一個短 tool call，不需要載 MCP schema。**Token 最省**——前提是
  agent 有 Bash。Microsoft README 跟 agent-browser README 都明確說在
  高頻 agent loop 上這勝過 MCP 路線。
- **MCP server**——Playwright MCP、`browser-use` MCP。Agent 用
  `mcp_call("playwright.click", {...})`。Schema 一次載完，比較適合沒
  Bash 的 agent，但要付 MCP overhead。每次呼叫的 token 比 CLI 高。
- **SDK**——Stagehand。寫 TypeScript 呼叫 `page.act("…")`。適合**寫進
  你的 application code**，不是 agent 隨叫隨用的 skill。

### 2. Snapshot 策略——a11y tree vs DOM vs vision

- **Accessibility-tree snapshot + element ref**（`playwright-cli`、
  `agent-browser`、Playwright MCP）。Agent 看到結構化的 tree + 穩定的
  `eN` / `@eN` ref。Token 便宜、可靠、不用脆弱 selector。
- **DOM + selector**（舊 Playwright / Selenium pattern）。Context 大、
  脆弱。
- **Vision-first**（`magnitudedev/browser-agent`，4k⭐）。Agent 看截圖
  推理。對 DOM 變化魯棒，但 token + 延遲都高；適合對抗看不透的 webapp。

### 3. 瀏覽器到底跑在哪

- **本地 Chromium**（所有 CLI 預設）——快、免費、用你機器。
- **本地 Chrome + 你的真實 profile**（`agent-browser`、`browser-use`）——
  看得到你真實的 cookie 跟登入狀態。強大，也是安全攻擊面。
- **雲端瀏覽器**——Vercel Sandbox / AWS Bedrock AgentCore
  (`agent-browser`)、Browser Use Cloud (`browser-use`)、Browserbase
  (`stagehand`)。按 session 計費；headless server、平行擴展、合規場景
  必需。

### 4. 持久 session vs 每次冷啟

- **持久 daemon**（`browser-use` CLI）——Chromium 在指令間保持開啟，
  ~50 ms/call。適合長 agent loop 在同一個站。
- **每次 session**（`playwright-cli` 預設、Playwright MCP）——乾淨啟停，
  one-shot 任務比較安全。每次延遲較高。

## 推薦對照

| 需求 | 選 |
|---|---|
| Token 省、有 Bash 的 agent 通用 browser CLI | `agent-browser` 或 `playwright-cli` |
| CI 已用 Playwright | `playwright-cli`（同一引擎、同一 selector） |
| 長期 session、最低 per-call 延遲 | `browser-use` CLI |
| Production agent、雲端平行瀏覽器 | `agent-browser`（Vercel/AWS）或 `stagehand`（Browserbase） |
| 頁面對抗 DOM scraping（重 canvas、anti-bot） | Vision-first（`magnitudedev/browser-agent`） |
| 想在 TypeScript app 內 code-level 控制 | `stagehand` SDK |
| Agent 沒 Bash，只有 MCP | Playwright MCP 或 `browser-use` MCP |

## 本 repo vendor 了什麼

**都沒有。** 記下來給未來的 agent 不要再爭：

- **安裝負擔重**——Chromium 下載、persistent profile、daemon process、
  可選的雲端帳號。Vendor 一個 SKILL.md **不會**幫你安裝底層 CLI；使用
  者還是要 `npm i -g agent-browser`、`pip install browser-use` 等。
- **per-project 比 user-global 好**——瀏覽器自動化 skill 常常碰到真實
  auth/cookie 跟站點 quirk。比較適合在 project 層級安裝，operator 可
  以先 review SKILL.md、hook、MCP config。
- **Security audit 警訊**——撰寫時 Skills.sh 顯示 `browser-use/browser-use`
  在 Gen Agent Trust Hub audit 失敗。先觀望。
- **Anthropic `webapp-testing` 已經涵蓋常見場景**——agent 驅動的
  webapp QA 已經有 [`anthropics/skills/webapp-testing`](../skills/webapp-testing.zh-TW.md)
  在 [`fullstack-nextjs`](../skills/index.zh-TW.md) series 裡，底層也是
  Playwright，但不綁特定 browser CLI。

真的需要的話，per-project 安裝：

```bash
# Token 省的 CLI 路線（推薦給 OpenCode / Claude Code / Codex）
npx skills add vercel-labs/agent-browser

# 持久 daemon 路線
npx skills add browser-use/browser-use

# 跟 CI Playwright test 同一引擎
npx skills add microsoft/playwright-cli
```

這些都能跟本 repo 的 research / SDD skill 共存——deep-research session
需要真瀏覽器時，`vendor/deep-research` 可以搭上面任何一個，無衝突。

## 延伸閱讀

- [Deep Research landscape](deep-research-landscape.zh-TW.md)——browser
  automation 是 deep-research stack 的第 4 層
- [SDD frameworks & agent harnesses](sdd-and-harnesses.zh-TW.md)——同樣
  的 CLI vs MCP vs framework 區分套到 spec-driven development
- [`anthropics/webapp-testing`](../skills/webapp-testing.zh-TW.md)——本
  repo 已 vendor 的 Playwright-based testing skill
- [Agent skill compatibility](agent-skill-compatibility.zh-TW.md)——上
  面所有 CLI 都遵守的 portable `SKILL.md` 規範
