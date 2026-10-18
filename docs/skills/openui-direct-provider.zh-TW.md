# openui-direct-provider

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這是 vendored [`openui`](openui.md) skill 的本地、provider 中立 (provider-neutral)
搭檔。它教 agent 在 app 裡加入 [OpenUI](https://www.openui.com/) generative UI，
同時**讓推論留在使用者自己的模型 provider**：OpenAI、Anthropic、Google，或任何
OpenAI 相容／本地端點。請求路徑上沒有任何託管服務。

## 為什麼需要它

官方 skill 預設導向付費的 OpenUI Gateway（見
[預設以 Gateway 為主](openui.md)）。OpenUI 的語言、prompt 產生器、parser 與
renderer 都是 MIT 授權的套件，可以搭配任何 provider。這個 skill 以這些套件和
MIT 授權的 [`thesysdev/openui`](https://github.com/thesysdev/openui) 文件為基礎，
並加上一條**中立規則**：只有在使用者主動問起，或需要只有它們才提供的功能時，
才提 Gateway 與 Autofix；即使提到，也會標明是付費託管服務，並說明自架的替代方案。

這組搭配類似 [`skill-author`](skill-author.md)（本地）與
[`skill-creator`](skill-creator.md)（vendored）：各管一半，互相 defer。兩個 skill
都會因為「OpenUI」被觸發，請依推論方式擇一安裝：

| 你想要 | 安裝 |
|---|---|
| 用自己的 provider、key 與儲存 | `openui-direct-provider` |
| OpenUI Gateway / Cloud、託管歷史、Reliability Monitoring | `openui` |

## 教什麼

- 核心流程：
  1. `defineComponent` / `createLibrary`
  2. `openui generate --spec`
  3. `generateSystemPrompt({ library, promptOptions })`，**不加** `cloud: true`
  4. provider 自己的 SDK
  5. 帶 `onAction` / `onError` 的 `<Renderer>`
- 後端範例（[`references/backend-recipes.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/openui-direct-provider/references/backend-recipes.md)）：OpenAI SDK、搭配任何 provider 的 Vercel AI SDK、OpenAI 相容／本地 base URL、純文字串流、LangGraph，各自配上對應的 Agent Interface stream adapter。
- 自架修復（[`references/self-repair.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/openui-direct-provider/references/self-repair.md)）：
  - 用 library 設計預防錯誤；
  - 用 streaming parser 或 `Renderer onError` 偵測；
  - 用使用者自己的模型做一次有上限的重試來修復。
- 常見陷阱：
  - agent 執行 `openui create` 會 scaffold **Cloud** 模板（請使用者自己在終端機互動選 *OpenUI Self-hosted*）；
  - CLI 會送 telemetry（可加 `--no-telemetry`）；
  - npm 版本落後 `main`；
  - model id 格式與 Gateway 不同；
  - UI 端 `Query`/`Mutation` 的參數不可信任。

## 安裝

```bash
npx skills@latest add daviddwlee84/agent-skills/skills -s openui-direct-provider
```

## Canonical SKILL.md

見
[`skills/local/openui-direct-provider/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/openui-direct-provider/SKILL.md)。
