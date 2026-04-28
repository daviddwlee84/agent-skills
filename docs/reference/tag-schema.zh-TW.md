# Tag schema (priority × effort) — 標籤 schema (priority × effort)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這是
[`skills/local/project-knowledge-harness/references/tag-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/tag-schema.md)
給人類讀者看的版本（agent 按需載入的是那一份）。內容相同，
這裡提供讓維護者不用挖進 skill 目錄。

兩條正交軸 (orthogonal axis) 防止「重要但無法實作」的陷阱。

## Priority

- `P1` —— 大概是下一個 batch（如果你今天坐下就會著手的）
- `P2` —— 值得做，但不急
- `P3` —— 有空再說 / nice-to-have
- `P?` —— 需要先評估；在決定 priority 前先做 spike

## Effort

- `S` —— 一小時內
- `M` —— 半天
- `L` —— 多天
- `XL` —— 架構性 (architectural)；寫 code 前必須先寫設計文件

## 有用的組合

- `P?` + `[?/L]` —— 顯式的「未知 priority、size 為 L」；最誠實的標籤
- `P3` + `[S]` —— 「小到任何空閒時間都能塞進去」
- `P1` + `[XL]` —— 警告「你說緊急但其實是巨無霸 —— 重新 scope」

## Heading 跟條目語法（validator 會檢查）

[`scripts/todo-kanban.sh`](scripts.md#todo-kanbansh) 強制這個精確
形式。完整文法在 [TODO format](todo-format.md)。簡短版：

- Section heading，依序：`## P1`、`## P2`、`## P3`、`## P?`、`## Done`
- `P1` / `P2` / `P3` 中的 active 條目：
  `- [ ] **[Effort] Title** — description`
- `P?` 中的 active 條目：
  `- [ ] **[?/Effort] Title** — description`
- `Done` 中的已交付 (shipped) 條目：
  `- ✅ [YYYY-MM-DD] [P#/Effort] Title — one-line shipped summary`
- active 條目可選的尾綴：
  `→ [research](backlog/<slug>.md)`

任何**不是**頂層 `- [ ]` / `- ✅` 條目的東西 —— 散文段落、blockquote、
HTML 註解、`---` 分隔線、縮排的 sub-bullet —— 都會被 validator 忽略。
利用這個彈性寫解釋性文字，不會破壞各 lane 的 machine-readability。
