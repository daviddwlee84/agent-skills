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

## Skill authoring

跟著 [`skill-author`](../skills/skill-author.md) 一起出貨；canonical
位於
[`skills/local/skill-author/scripts/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/skill-author/scripts)。
**沒有**鏡射到頂層 `scripts/`，因為這是 skill author 用的工具，不是 repo
範圍的 make target。

### `new-skill.sh`

```bash
bash skills/local/skill-author/scripts/new-skill.sh <skill-name>
bash skills/local/skill-author/scripts/new-skill.sh --project my-skill
bash skills/local/skill-author/scripts/new-skill.sh --global my-skill
bash skills/local/skill-author/scripts/new-skill.sh --local --vendor cherry-picked
bash skills/local/skill-author/scripts/new-skill.sh --dry-run my-skill
```

從 template scaffold 出 canonical 的 skill 目錄（`SKILL.md` +
`references/` + `scripts/` + `assets/`），並為 non-universal agents 加上
**相對 (relative)** 的 discovery symlinks。Script 從 CWD 往上走自動挑
placement scope；顯式 flag 可覆寫。

Placement scopes（完整表格見
[creating local skills](../workflows/creating-local-skills.md)）：

- **LOCAL** —— 往上找到 publishing-repo anchor（`vendor.yaml` /
  `skills/local/` / `skills/.claude-plugin/`）。Canonical 放在
  `<repo>/skills/local/<name>/`（搭 `--vendor` 則放 `skills/vendor/`）；
  symlinks 給 `.agents/skills/` 跟 `.claude/skills/`。
- **PROJECT** —— 往上找到 `.git`。Canonical 放在
  `<repo>/.agents/skills/<name>/`；symlink 給 `.claude/skills/<name>`
  （加上 repo root 已存在的其他 non-universal agent dir）。
- **GLOBAL** —— 找不到 anchor 或顯式 `--global`。Canonical 放在
  `~/.agents/skills/<name>/`；symlinks 給 `~/.claude/skills/<name>` 跟
  `$HOME` 下已存在的其他 non-universal agent dir。

Symlink fan-out 遵循 `npx skills add` 的紀律：「claude-code 永遠加；其他
agent 只在它的 config root 已存在於 base dir 時才加」——絕不為使用者
其實沒在用的 agent 建立新的 `.windsurf/` 之類目錄。每個 symlink
建立後會用 `test -e <link>/SKILL.md` 驗證；dangling link 直接 exit 4。

Flags：

- `--local` / `--project` / `--global` —— 強制 scope（互斥）。
- `--vendor` —— 只在 LOCAL 有效；改用 `skills/vendor/<name>/`。
- `--root DIR` —— 覆寫 walk-up 起點。
- `--no-symlinks` —— 跳過 agent dir fan-out。
- `--dry-run` —— 印出所有動作但不寫檔。
- `--force` —— 覆寫 canonical dir 並取代已存在的 symlinks。

Output：stdout 單一 JSON 物件
（`{skill, mode, canonical, symlinks[], next_steps[]}`）；prose 走
stderr。

Exit codes：`0` ok；`1` 參數錯誤；`2` canonical dir 已存在（用
`--force`）；`3` scope 前提沒過（例如 `--project` 卻不在 git repo
裡）；`4` 寫完 symlink 驗證失敗（就是
[symlink-target-relative 那個坑](../reference/pitfalls.md)）。

### `lint-skill.sh`

```bash
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/<name>
bash skills/local/skill-author/scripts/lint-skill.sh --strict skills/local/<name>
bash skills/local/skill-author/scripts/lint-skill.sh --json   skills/local/<name>
```

檢查一個 skill 目錄的 frontmatter + 長度、script hygiene
（shebang / +x / `--help` handler）、reference 可達性。完整 checklist
見 [`skill-author`](../skills/skill-author.md)。

### `lint-frontmatter.sh`

```bash
make lint-frontmatter                                  # 掃過整個 skills/
./scripts/lint-frontmatter.sh skills/local/<name>/SKILL.md
./scripts/lint-frontmatter.sh --parser node skills     # 跟 npx skills 用同一顆 parser
```

把指定路徑底下每個 `SKILL.md` 的 frontmatter 真的丟給 YAML parser 解析，
並確認 root 是 mapping、`name` 與 `description` 都是字串。單一 skill 的
情況 `lint-skill.sh` 會直接呼叫它。

之所以需要這支：frontmatter 解析失敗時各家 harness 是**默默跳過**那個
skill——`npx skills add` 只印一行 `⚠ Skipped … YAML parse error`，exit code
仍然是 `0`。最常見的原因是沒加引號的 `description:` 裡出現 `": "`；沒加引號
的值裡出現 ` #` 更陰險，因為它解析得過，但 description 會被當成註解從那裡
截斷（所以只報 warning，不是 error）。詳見
[pitfalls](../reference/pitfalls.md)。

Parser 會自動偵測：`yq` → PyYAML → js 的 `yaml` 套件（`npx skills` 自己用
的那顆，可用 `--parser node` 強制指定）。三個都沒有時會退化成 pattern
heuristic，並在輸出裡講明。

Exit codes：`0` 全過；`1` 至少一個檔案失敗；`2` 參數錯誤、路徑不存在，或
指定的 parser 不可用。

### `git-hooks/pre-push`

```bash
make install-hooks     # symlink 到 .git/hooks/pre-push
git push --no-verify   # 單次略過
rm .git/hooks/pre-push # 移除
```

跑 `make validate`（frontmatter + `marketplace.json` + `TODO.md` 格式），
失敗就中止 push 並印出輸出尾巴。跟
[`.github/workflows/validate.yml`](https://github.com/daviddwlee84/agent-skills/blob/main/.github/workflows/validate.yml)
是同三道關卡（CI 在 push 與 PR 時跑）；hook 只是把訊號往前挪——畢竟壞掉的
`SKILL.md` 在安裝當下是看不見的。
