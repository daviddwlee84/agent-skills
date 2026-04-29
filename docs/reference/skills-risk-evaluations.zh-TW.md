# Skill risk evaluations on skills.sh — skills.sh 上的 skill 風險評估

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

[skills.sh](https://skills.sh/daviddwlee84/agent-skills) 對這個 repo 裡每個
skill 跑三組獨立的 audit，把結果展示在 catalog 頁面：

| Auditor | 檢查什麼 |
| ------- | -------- |
| **Gen** (Agent Trust Hub) | Gen 自家模型給出的高層次「這個 skill 裝下去安全嗎？」評論。 |
| **Socket** | 對 skill 檔案做靜態掃描，找 credential 形狀字串、可疑 install script、網路呼叫、混淆碼等。 |
| **Snyk** | 標準 CVE / SCA 對宣告的 dependency 跑，再加一組 AI-skill 專用規則 (W0xx)，針對 prompt injection / agent-facing 風險。 |

這頁記錄**目前的 finding** 與每一條的判讀理由，讓讀者（或未來的我）不用每次都重新推一遍
這個 flag 是真風險還是預期內的雜訊。

## 目前的 finding

以 [skills.sh/daviddwlee84/agent-skills](https://skills.sh/daviddwlee84/agent-skills)
最近一次 audit 為準：

| Skill | Gen | Socket | Snyk |
| ----- | --- | ------ | ---- |
| `mkdocs-site-bootstrap`     | Safe | 0 alerts | **Med Risk** |
| `project-knowledge-harness` | Safe | 0 alerts | Low Risk |
| `agent-history-hygiene`     | Safe | **1 alert** | Low Risk |

兩條被標的項目都是**預期內**，根因是 skill 的核心功能本身，不是真漏洞。下面是判讀。

## `agent-history-hygiene` — Socket 1 alert（預期內）

- **觸發檔案：** `tests/fixtures/real_anthropic.md`
- **Pattern：** Anthropic API key 形狀 (`sk-ant-api03-aaaa…AA`)
- **Severity：** medium / confidence high

這個 skill 的核心職責就是偵測並 redact agent transcript 與 plan 檔裡的秘密。
要驗 `gitleaks` 規則 + `redact_secrets.py` 的替換邏輯真的會 fire，就需要一份**故意做得很像
真的**的秘密形狀字串作為 corpus。`tests/fixtures/` 因此刻意放了：

- `real_anthropic.md` — `sk-ant-api03-` 後面跟 93 個 filler 字元再加 `AA`，
  剛好是嚴格 Anthropic 規則要求的形狀
- `real_openai.md` — `sk-proj-` + 100 字元，命中 OpenAI project-key 規則
- `private_key.md` — 假的 `-----BEGIN RSA PRIVATE KEY-----` block

Socket 的 secret-pattern scanner 沒辦法分辨「全 `a` 的 placeholder filler，本來就是要被
match 的」與「外洩的真 credential」，所以會在這個 fixture 上 fire。把 corpus 拿掉會默默
弄壞測試套件，等於把整個 skill 的存在意義抹掉。所以**保留** alert。

如果在 downstream dashboard 上太礙眼，可以在 skills.sh / Socket 把它標 false positive，
理由寫「intentional secret-shape test corpus for a secret-redaction skill」。

## `mkdocs-site-bootstrap` — Snyk Med Risk（預期內）

這條**不是** transitive dependency 的 CVE — pin、bump、或拔掉某個 package 都不會改變
分數。

- **Rule：** `W011` — Third-party content exposure / indirect prompt injection
- **Risk score：** 0.90
- **Snyk 原文理由：**
  > The agent will read untrusted, user-generated third-party docs that could
  > contain instructions and thus enable indirect prompt injection.

這個 skill 的 template 預設裝 `mkdocs-llmstxt` 與 `mkdocs-copy-to-llm`，會產出：

- `/llms.txt` 與 `/llms-full.txt` — 給 LLM 吃的全內容 dump
- 每頁的 "copy as markdown for LLM" 按鈕

任何吃這些端點的 LLM agent 等於在讀 `docs/` 裡有什麼。如果 `docs/` 收外部貢獻（例如
open-source PR），攻擊者可以在某個 doc 頁面埋 prompt injection payload，然後讓那段內容
流進下游 agent 的 context。Snyk 的 W0xx ruleset 標的就是這個 agent-facing 表面。

### 為什麼接受這個分數

整個 dogfood `mkdocs-llmstxt` + copy-to-llm 的目的就是讓 docs 對 LLM 友善；削弱這層就等於
把 skill 的價值砍掉。真正的修法是**威脅建模 (threat modeling)**，不是改 dependency：

- 把 `docs/` 當作 LLM 輸入邊界（在 `docs/**` 上設 CODEOWNERS、外部 PR 一律走 review）。
- 在 skill 文件裡寫清楚這個威脅，讓下游使用者**知情**地 opt in。

未來給 `init-docs-site.sh` 加一個 opt-out flag（例如 `--no-llmstxt`，給不需要 LLM-facing
表面的 repo 用）已經記在 `TODO.md`，不會搶在前面 land。

### 延伸閱讀

- [`reference/mkdocs-2-and-zensical.md`](mkdocs-2-and-zensical.md) — 為什麼 pin
  `mkdocs<2`（不同理由，同個 skill）。
- [`reference/docs-stack-recipe.md`](docs-stack-recipe.md) — bootstrap 實際裝了什麼。

## 為什麼還沒上 README badge

skills.sh **目前沒有 first-party badge endpoint**。我們探過幾條常見路徑，全部 404：

```
https://skills.sh/<owner>/<repo>/badge.svg          → 404
https://skills.sh/badge/<owner>/<repo>.svg          → 404
https://skills.sh/api/badge/<owner>/<repo>          → 404
```

如果之後想在 `README.md` 上一排 audit badge，有三條路，由輕到重：

1. **`shields.io` 靜態 badge + 手刻連結。** 每條 badge 的內容（`Safe`、
   `1 alert`、`Med (W011)`）手寫，圖片連到 skills.sh 詳情頁。零基礎建設，但 audit
   一重跑就會 drift。
2. **`shields.io` `endpoint` schema + 自架 JSON。** 排程 GitHub Action 抓 skills.sh，
   把 `badges/{gen,socket,snyk}.json` 寫到 `gh-pages`，shields.io 的
   [endpoint badge](https://shields.io/badges/endpoint-badge) 對著那份 JSON 渲染。
   會自動更新，建置成本約半天。
3. **直接用 Snyk / Socket 官方 badge。** Snyk 與 Socket 都各自出 badge，但他們的
   scope 是 whole-repo 或 npm-package，不對應 skills.sh 的 per-skill 觀點，意義不一樣。

三條都先擱著。等到 (a) skills.sh 出 first-party badge endpoint，或 (b) audit 訊號變成
trust 決策的關鍵（例如外部貢獻者會看 verdict 決定要不要裝），再回頭評估。

## 什麼時候該回來更新這頁

- 新 skill landed，第一次拿到非平凡的 audit verdict。
- 既有 finding 翻盤（例如 Socket 規則更新後 alert 消失，或新的 W0xx fire）。
- skills.sh 換 auditor 陣容，或開始發 badge URL。
