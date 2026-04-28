# Bundled scripts — 附帶的 script

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這個 repo
[`scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/scripts)
目錄裡的每一個 script 也都被打包進擁有它的 skill 內（這樣透過
`npx skills` 出貨的 package 才能維持自包含 (self-contained)）。
這對副本必須保持 byte-identical —— 詳見 [Conventions](../conventions.md)。

Script 用 **Bash 3.2** 寫（這樣才能在沒裝 homebrew bash 的原生 macOS 上跑）。

## Vendor 系統

### `add-vendor.sh`

```bash
./scripts/add-vendor.sh owner/repo/path/to/skill
./scripts/add-vendor.sh https://github.com/owner/repo/tree/branch/path/to/skill
./scripts/add-vendor.sh --name custom --branch dev owner/repo/skills/some-skill
./scripts/add-vendor.sh --no-sync owner/repo/path/to/skill
```

透過 `gh api` 驗證 upstream 路徑存在、對
[`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
中既有條目去重 (deduplicate)、追加新條目、並觸發 `sync-vendor.sh`
（用 `--no-sync` 跳過）。

**依賴項目：** `gh`（已認證）跟 `yq`。

### `sync-vendor.sh`

```bash
./scripts/sync-vendor.sh           # 下載所有 vendored skill
./scripts/sync-vendor.sh --check   # dry-run：報告哪些條目有 upstream 新 commit
```

迭代 `vendor.yaml`，透過 GitHub trees API 下載每個 skill，
成功時更新 `last_sync.{date,commit}`。`--check` 印出會改變什麼但不寫入。

## Project memory

這些隨
[`project-knowledge-harness`](../skills/project-knowledge-harness.md)
出貨；canonical 副本在
[`skills/local/project-knowledge-harness/scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/project-knowledge-harness/scripts)。

### `todo-kanban.sh`

```bash
./scripts/todo-kanban.sh                    # 預設：TODO.md，Markdown 看板
./scripts/todo-kanban.sh path/to/TODO.md    # 顯式指定檔案
./scripts/todo-kanban.sh --validate-only    # 只回 exit code，不渲染
./scripts/todo-kanban.sh --json             # 機器可讀的 lane 摘要
```

驗證 [TODO format](todo-format.md) 並渲染看板樣式 (kanban-style) 的板子
到 stdout。任何不是頂層 `- [ ]` / `- ✅` 條目的東西都會被忽略，
所以你可以在 section heading 底下灑點散文。

Exit code：`0` 有效；`1` 驗證失敗（行號印到 stderr）；`2` 用法錯誤。

### `add-todo.sh`

```bash
./scripts/add-todo.sh \
  --priority P3 \
  --effort M \
  --title "Add docs versioning" \
  --description "Use mike for versioned docs"

./scripts/add-todo.sh \
  --priority "P?" \
  --effort "?" \
  --title "Try Rspress for docs" \
  --description "Evaluate AI-native docs framework alternative"

./scripts/add-todo.sh \
  --priority P2 --effort L \
  --title "Migrate kanban to Python" \
  --description "Bash 3.2 compat is getting expensive" \
  --backlog
```

把符合 canonical 格式的條目插入到對應的 `## P*` lane。
帶 `--backlog` 時也會從 skill template 產生 `backlog/<slug>.md`，
並在新行尾追加 ` → [research](backlog/<slug>.md)`。

寫入後重新跑 validator。如果驗證失敗，原本的 `TODO.md` 會被還原。

Flag：

- `--priority {P1|P2|P3|P?}` —— 必要。
- `--effort {S|M|L|XL|?}` —— 必要。`?` 只在 `P?` 時有效。
- `--title TEXT` —— 必要。不能含 `*`。
- `--description TEXT` —— 必要。em-dash 後是自由形式。
- `--backlog` —— 同時建立 backlog 研究文件。
- `--file PATH` —— TODO 檔案 (預設 `TODO.md`)。
- `--dry-run` —— 把改寫後的檔案印到 stdout，不修改原檔。

### `promote-todo.sh`

```bash
./scripts/promote-todo.sh \
  --title "<substring of the item's title>" \
  --summary "<one-line shipped summary>"
```

原子性地把 active 條目從其 lane 搬到 `## Done`，使用日期化的
`Done` 語法，並重新驗證。如果 substring 匹配 0 個或多於一個
active 條目就拒絕執行 —— 把 substring 寫精準一點。

Flag：

- `--title SUBSTRING` —— 必要。標題的 case-sensitive substring。
- `--summary TEXT` —— 必要。
- `--file PATH` —— TODO 檔案 (預設 `TODO.md`)。
- `--date YYYY-MM-DD` —— 覆寫完成日期 (預設：今天，UTC)。
- `--dry-run` —— 印到 stdout，不修改檔案。
- `--validator PATH` —— 覆寫 validator 路徑 (預設：sibling `todo-kanban.sh`)。

### `sweep-inbox.sh`

```bash
./scripts/sweep-inbox.sh                # backlog/inbox.md 的互動式分流
./scripts/sweep-inbox.sh --dry-run      # 預覽不修改 inbox 或 TODO
./scripts/sweep-inbox.sh --batch        # 非互動：跳過需要 prompt 的行
```

逐行讀
[`backlog/inbox.md`](https://github.com/daviddwlee84/agent-skills/tree/main/backlog)。
對每一行非空、非註解的行，prompt 詢問 priority / effort / 正式
title / description（盡量提供預設），呼叫 `add-todo.sh`，並在條目
被 commit 後從 inbox 移除該行。

`--batch` 是設計給 agent 工作流程：當行能推斷出 `priority:` /
`effort:` / `title:` / `description:` 就自動形式化；模糊的留在 inbox
等下一次互動式 sweep。

Inbox 行慣例（全部可選；零散行也接受）：

```text
# 註解跟空行被忽略。
- maybe add docs versioning with mike
- priority=P3 effort=M title="Add docs versioning" desc="Use mike for versioned docs"
- the find-skills bootstrap UX is rough
```

第一種需要互動 prompt。第二種完全可解析，在 `--batch` 模式有效。

### `init.sh`

只住在 skill 內（**沒有**鏡射到頂層 `scripts/`）：
[`skills/local/project-knowledge-harness/scripts/init.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/scripts/init.sh)。

```bash
skills/local/project-knowledge-harness/scripts/init.sh \
  --target /path/to/project \
  --project-name "My Project" \
  --deployment chezmoi   # 或 npm | pip | docker | none
```

對任何目標 repo 一次設置 `TODO.md` + `backlog/` + `pitfalls/` +
agent 指引片段 + README 片段。Idempotent。完整 flag 列表見
[`project-knowledge-harness`](../skills/project-knowledge-harness.md)。
