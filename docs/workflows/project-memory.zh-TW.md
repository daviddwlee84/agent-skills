# Project memory workflow — 專案記憶工作流程

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁說明如何在這個 repo 的
[`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)、
[`backlog/`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog)、
[`pitfalls/`](https://github.com/daviddwlee84/agent-skills/tree/main/pitfalls)
裡新增與維護條目。同樣的工作流程也適用於任何跑過
[`project-knowledge-harness` 的 `init.sh`](../skills/project-knowledge-harness.md)
的 project。

## 三種新增 TODO 的方式

| 方式 | 適用情境 | 驗證 |
|---|---|---|
| **`scripts/add-todo.sh`** | 已知 priority + effort 的結構化條目 | 強制執行 —— 拒絕寫入格式不符的條目 |
| **`backlog/inbox.md`** | 維護者快速捕獲；「之後再分流 (triage)」 | 無 —— 之後由 `sweep-inbox.sh` 形式化 |
| **直接編輯 `TODO.md`** | 大量導入；熟悉格式規範的 agent | 編輯後跑 `make kanban` 抓 drift |

`add-todo.sh` 跟 inbox sweeper 隨
[`project-knowledge-harness`](../skills/project-knowledge-harness.md)
skill 出貨，並鏡射到頂層 [`scripts/`](../reference/scripts.md)。

### 方式 1 — `scripts/add-todo.sh`

```bash
./scripts/add-todo.sh \
  --priority P3 \
  --effort M \
  --title "Add docs versioning" \
  --description "Use mike for versioned docs"

# P? 條目用 --unknown-priority；effort 也可以是 unknown：
./scripts/add-todo.sh \
  --priority "P?" \
  --effort "?" \
  --title "Try Rspress for docs" \
  --description "Evaluate AI-native docs framework alternative"

# 同時建立一份 backlog 研究文件
./scripts/add-todo.sh \
  --priority P2 \
  --effort L \
  --title "Migrate kanban to Python" \
  --description "Bash 3.2 compat is getting expensive" \
  --backlog
```

它做的事：

1. 為選擇的 lane 組出 canonical 的條目行。
2. 插入到 `TODO.md` 中對應的 `## P?` heading 底下。
3. 如果有 `--backlog`，從 skill 的 `assets/backlog-doc.md.template`
   產生 `backlog/<slug>.md`，並在新 TODO 行尾追加
   ` → [research](backlog/<slug>.md)`。
4. 重新跑 validator。如果驗證失敗，原本的 `TODO.md` 會被還原。

完整 flag 列表見 [`scripts/add-todo.sh --help`](../reference/scripts.md#add-todosh)。

### 方式 2 — `backlog/inbox.md`

當你還不知道 priority / effort 的零散捕獲：

```bash
echo "- maybe add docs versioning with mike" >> backlog/inbox.md
echo "- the find-skills bootstrap UX is rough" >> backlog/inbox.md
```

`inbox.md` 內什麼都行 —— 散文、橫線清單、半成形的想法。
validator **不會**看這個檔案。

當你（或 agent）準備分流時：

```bash
./scripts/sweep-inbox.sh
```

sweeper 會逐行讀 `inbox.md`，為每行詢問 priority / effort / 正式
title / description，呼叫 `add-todo.sh`，並在條目被形式化後從 inbox
移除該行。`--dry-run` 可以預覽而不修改任何檔案。

如果你跟 agent 一起工作，更簡單的方式是直接說：「sweep the inbox」
或「clear `backlog/inbox.md`」。
[`project-knowledge-harness`](../skills/project-knowledge-harness.md)
的 SKILL.md 會指示 agent 調用 `sweep-inbox.sh`，並一條一條跟維護者
詢問缺失欄位。

### 方式 3 — 直接編輯 `TODO.md`

有時這是最快的路徑。格式小到可以背：

```markdown
## P2

- [ ] **[M] Title here** — description goes after the em-dash

## P?

- [ ] **[?/L] Unsure-priority item** — description
```

編輯後跑 `make kanban`（或 `./scripts/todo-kanban.sh --validate-only`）
在 commit 前抓出 typo。完整文法在
[Reference → TODO format](../reference/todo-format.md)。

## 完成條目的提升 (Promoting)

當你交付 (ship) 一個 TODO 條目時，在同一個 commit：

```bash
./scripts/promote-todo.sh \
  --title "<substring of the item's title>" \
  --summary "<one-line shipped summary>"
```

這會原子性地把匹配到的 active 條目搬到 `## Done`，使用日期化的
`Done` 語法，並重新驗證。如果 substring 匹配 0 個或多個 active
條目，它會拒絕執行 —— 出錯就把 substring 寫精準一點。

如果該條目有對應的 `backlog/<slug>.md`，在同一個 commit 把它的
`Status:` 設為 `shipped` —— **不要刪除**。歷史研究經常會啟發
相關決策。

## 何時要寫 `backlog/` 文件

當對話產生了之後值得回頭再讀的東西時：研究筆記、設計取捨
(trade-off)、失敗 spike 的錯誤 trace、廠商比較表。TODO 行是 *index*；
backlog 文件是 *內容*。

一個有用的判斷準則：「**三個月後重看，光憑 TODO 那一行夠嗎？**」
如果不夠，就寫 backlog 文件。

skill 的
[`references/when-to-add-docs.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/when-to-add-docs.md)
有完整決策樹。

## 何時要寫 `pitfalls/` 文件

當你剛除錯完一個非顯而易見、且合理可能再發生的問題時，**立刻**寫
`pitfalls/<symptom-slug>.md`。標題應該是**症狀**（你會丟進搜尋框
的字串），不是 root cause。

逐字複製錯誤訊息 —— **不要**改寫，會殺掉 grep-ability。

如果這個陷阱很嚴重（靜默資料毀損、跨機器復發、非顯而易見的
workaround），把它升級成 `AGENTS.md` / `CLAUDE.md` 中的硬性
不變條件 (Hard invariant)。pitfall 文件留作歷史紀錄；
invariant 才是防止復發的規則。
