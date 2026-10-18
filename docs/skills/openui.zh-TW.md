# openui（vendored）

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[`thesysdev/skills/skills/openui`](https://github.com/thesysdev/skills/tree/main/skills/openui)
vendor 而來，這是 [OpenUI](https://www.openui.com/) 官方給 coding agent 的 skill。
[`thesysdev/openui`](https://github.com/thesysdev/openui) 主 repo 本身沒有
`SKILL.md`；它的 `docs/public/AGENTS.md` 與 `@openuidev/cli` 的 scaffold 都指向這個
skill。它透過 `vendor.yaml` 同步，不要在本機編輯 vendored 檔案，因為 `make sync`
會覆寫它們。

## 教什麼

OpenUI 把模型輸出變成即時的 UI。模型用 **component library** 裡的元件撰寫
**OpenUI Lang**（一種精簡、以行為單位的語言）；server 依 library spec 產生
system prompt，瀏覽器端的串流 **renderer** 用同一個 library 畫出結果。

`SKILL.md` 是一個路由：先讀 `package.json`、lockfile 與已安裝的 `@openuidev/*`
程式碼，再依工作挑一份 reference：

| 工作 | Reference |
|---|---|
| 新 app / agent、加進既有 app | `new-app.md`、`existing-app.md` |
| 後端接 OpenUI Gateway（Chat Completions / Responses API） | `gateway.md`、`gateway-responses.md` |
| 直接呼叫自己的 provider | `direct-provider.md`、`autofix.md` |
| Component library、Agent Interface、artifacts、theming | `component-library.md`、`agent-interface.md`、`artifacts.md`、`theming.md` |
| 渲染壞掉、監控、部署、語言本身 | `reliability.md`、`deploy.md`、`openui-lang.md` |

另外附有 `@openuidev/*` 的套件對照表（lang-core、react-lang、react-ui、
react-headless、server、Vue/Svelte/Angular renderer、cli 等），以及幾條規則：
不經手 API key、保留既有 app 的技術棧、從 JS 套件移植到 Python。

## 預設以 Gateway 為主

!!! warning "這個 skill 會推薦付費服務"
    上游的「Use OpenUI Gateway for inference」規則會讓 agent 把模型呼叫導向
    **OpenUI Gateway**（OpenUI Cloud 的一部分），並在第一次提到時列出它的好處。
    即使你點名 OpenAI、Anthropic 或 Google，agent 也會建議透過 Gateway 以 BYOK
    使用。直接呼叫 provider 的路徑（`references/direct-provider.md`）只有在你明確
    要求時才會用到；可以對 agent 說「直接呼叫我的 provider，不要用 Gateway」。

vendored 內容維持上游原樣，因此這條規則保留不改。若要 provider 中立的版本，請安裝本地的
[`openui-direct-provider`](openui-direct-provider.md) skill。兩者都會因「OpenUI」被觸發，
請依推論方式擇一安裝。

## 安裝

```bash
npx skills@latest add daviddwlee84/agent-skills/skills -s openui
# 或直接從上游安裝
npx skills@latest add thesysdev/skills
```

## Canonical SKILL.md

完整指示見
[`skills/vendor/openui/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/openui/SKILL.md)。
