# Pitfalls format — Pitfalls 格式

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

`pitfalls/` 目錄收錄你已經除錯過一次的非顯而易見陷阱 (pitfall)，
這樣下一個 agent（或未來的你）可以 grep 該症狀，直接跳到修正方式。

這頁文件化
[`project-knowledge-harness`](../skills/project-knowledge-harness.md)
所使用的格式。任何跑過該 skill `init.sh` 的 project 都採用同一形狀。

## 檔案佈局

```
pitfalls/
├── README.md                              # 索引 + 交叉引用 (cross-reference) 表
├── <symptom-slug-1>.md                    # 一個陷阱一個檔案
├── <symptom-slug-2>.md
└── …
```

slug 是 **症狀 (symptom)**，不是 root cause。你以你看到的錯誤來搜尋，
不是用最終學到的解釋來搜尋。

## 單一 pitfall 文件 —— 必要區段

每個 `pitfalls/<slug>.md` 應該按順序回答四個問題：

1. **症狀 (Symptom)** —— 逐字 (verbatim) 的錯誤文字或行為。複製貼上，
   **不要改寫**。改寫會殺掉 `grep`。
2. **Root cause** —— 底層機制，一兩段話帶過。
3. **Workaround** —— 復原的精確步驟。適用時用 code block。
4. **預防 (Prevention)** —— 套用後可以預防陷阱的不變條件 (invariant)。
   如果預防嚴重到（靜默毀損、跨機器復發），把它升級成
   `AGENTS.md` / `CLAUDE.md` 的硬性 invariant，然後雙向連結。

完整 template 在
[`skills/local/project-knowledge-harness/assets/pitfall-doc.md.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/assets/pitfall-doc.md.template)。

## 標題 / slug 指引

把標題寫成搜尋 query 會長的樣子：

| ✅ 症狀為先 | ❌ Root-cause 為先 |
|---|---|
| `gh-api-404-on-tree-endpoint.md` | `vendor-yaml-branch-handling.md` |
| `npx-skills-empty-after-install.md` | `skills-discovery-depth-fallback.md` |
| `mkdocs-strict-fails-on-relative-md.md` | `mkdocs-link-validation-rules.md` |
| `mkdocs-i18n-llms-files-are-empty.md` | `mkdocs-plugin-lifecycle-collision.md` |

讀 pitfall 的 agent 在問的問題是：「我剛碰到的就是這個嗎？」 ——
標題要符合那個問題，不是答案。

目前 repo 裡的例子是
[`mkdocs-i18n-llms-files-are-empty.md`](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/mkdocs-i18n-llms-files-are-empty.md)：
看得見的症狀是 llms 輸出幾乎為空或語言錯誤；底層的 plugin lifecycle
collision 應寫在文件裡，不應放進 slug。

## 不要使用 `pitfalls/` 的時機

- **已經修好的 project-specific bug。** 改用 `git log` / CHANGELOG。
  pitfall 是給可能會復發的陷阱用的。
- **入門 (onboarding) 缺口。** 那是文件，放在 `docs/` 或 README。
- **沒有具體症狀的「需要注意的事項」清單。** 沒有具體症狀就沒有東西
  可以 grep，pitfall 就沒有發揮作用。

## 交叉引用 (cross-referencing)

`pitfalls/README.md` 應該維護一份小表格，列出住在目錄**外**的 pitfall
—— 例如某個設計文件中已說明的已知陷阱。表格讓未來的 agent 可以從
一個地方 grep 症狀關鍵字，即使解釋住在別處。
