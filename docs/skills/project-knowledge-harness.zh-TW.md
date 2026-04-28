# project-knowledge-harness

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

一個輕量、檔案為基礎 (file-based) 的記憶 harness，給任何軟體 project
三個界線分明的介面：

| 介面 | 時間方向 | 它回答的問題 | 存取模式 |
|---|---|---|---|
| `TODO.md` | 未來 | 「我們之後可能會做什麼？」 | 由上往下讀 (priority lane) |
| `backlog/<slug>.md` | 未來 | 「這個想法背後的分析是什麼？」 | 從 `TODO.md` 索引 |
| `pitfalls/<slug>.md` | **過去** | **「我看到錯誤 X —— 以前發生過嗎？」** | **Grep 症狀關鍵字** |

這個 skill 存在是為了阻止兩種常見失敗：有價值的調查從對話歷史蒸發，
以及 `IDEAS.md` / `ROADMAP.md` / `WISHLIST.md` / `LESSONS.md` 那種沒人
維護的檔案墳場。

## skill 觸發時機

未來方向訊號：「想法該放哪？」、「之後再說」、「nice to have」、
「工程量太大需要再評估」、「先記下來」。

過去方向訊號：「保存這次除錯紀錄」、「踩過的坑」、`docs/` 裡到處是
散亂的「Common issues」區段。

任一：「有個地方放 X 嗎？」其中 X 是關於決策或歷史的 metadata，而非
當前功能。

## skill 自身的結構

```
skills/local/project-knowledge-harness/
├── SKILL.md                      # ~170 行的進入點；activation 時載入
├── assets/                       # 複製到目標 project
│   ├── TODO.md.template
│   ├── backlog-README.md.template
│   ├── backlog-doc.md.template
│   ├── pitfalls-README.md.template
│   ├── pitfall-doc.md.template
│   ├── agent-guidance.md.template   # 給 AGENTS.md / CLAUDE.md 的片段
│   └── readme-roadmap.md.template   # 給 README.md 的片段
├── scripts/                      # 在 setup 時或被 agent 執行
│   ├── init.sh                   # 上述全部的一次性 setup
│   ├── todo-kanban.sh            # validator + Markdown / JSON 看板渲染器
│   └── promote-todo.sh           # 原子性 active → ## Done 搬移 + 重新驗證
└── references/                   # 從 SKILL.md 連結按需載入
    ├── tag-schema.md             # priority × effort schema 與精確語法
    ├── when-to-add-docs.md       # backlog vs pitfall vs invariant 決策規則
    ├── anti-patterns.md          # 該避免的錯誤
    └── deployment-exclusion.md   # 各部署機制的 ignore-rule 快查
```

`SKILL.md` 刻意短，並指向 `references/*.md`，這樣 agent 只在需要時才
載入決策細節（[漸進式揭露 (progressive disclosure)](https://agentskills.io/specification#progressive-disclosure)）。

## 在新 repo 套用 skill

預設工作流程是一行指令：

```sh
skills/local/project-knowledge-harness/scripts/init.sh \
  --target /path/to/project \
  --project-name "My Project" \
  --deployment chezmoi   # 或 npm | pip | docker | none
```

這是 idempotent 的 —— 重複跑會 skip 已經存在的檔案、以及 sentinel
marker 已存在的片段。傳 `--force` 來覆寫三個 template 檔；片段仍然
只會 append 一次。

`init.sh` 做的事：

1. 從 `assets/*.template` 渲染 `TODO.md`、`backlog/README.md`、
   `pitfalls/README.md`，替換 `<PROJECT NAME>`、
   `<DEPLOYMENT MECHANISM>`、`<IGNORE FILE>`。
2. 把 agent 指引片段 append 到 `AGENTS.md` / `CLAUDE.md`
   (自動偵測；用 `--agent-contract` 覆寫)。
3. 把 "Roadmap & lessons learned" 片段 append 到 `README.md`
   (用 `--readme ""` 跳過)。
4. 跑 `todo-kanban.sh --validate-only TODO.md` 確認檔案是 machine-readable。
5. 印出你應該加到 ignore 檔的部署相關行。

`init.sh` 刻意**不**編輯 `.gitignore` / `.chezmoiignore.tmpl` /
`.dockerignore` —— 這對自動化工具來說爆炸半徑太大。把印出的快查當
成你的 TODO。

## Bundled scripts 細節

### `scripts/todo-kanban.sh`

驗證格式並渲染看板樣式的板子。

```sh
scripts/todo-kanban.sh                    # 預設：TODO.md，Markdown 看板
scripts/todo-kanban.sh path/to/TODO.md    # 顯式檔案
scripts/todo-kanban.sh --validate-only    # 只回 exit code
scripts/todo-kanban.sh --json             # 機器可讀的 lane 摘要
```

驗證規則：

- 第一個非空 heading 必須是 `# TODO`。
- Section 必須按順序：`## P1`、`## P2`、`## P3`、`## P?`、
  `## Done`。`## Done` 之後允許額外 heading (例如 `## Notes` 或 prune
  log section)。
- 頂層 list 條目會被驗證：
  - `P1` / `P2` / `P3`：`- [ ] **[Effort] Title** — description`
  - `P?`：              `- [ ] **[?/Effort] Title** — description`
  - `Done`：            `- ✅ [YYYY-MM-DD] [P#/Effort] Title — summary`
  Effort 是 `S`、`M`、`L`、`XL` 之一。Active 條目可以 `→ [research](backlog/<slug>.md)` 結尾。
- 任何**不是**頂層 `- [ ]` / `- ✅` 條目的東西 —— 散文、blockquote、
  HTML 註解、`---` 分隔線、縮排 sub-bullet —— 都會被忽略，不會列入 lane
  總數。這讓你在每個 section 底下寫內聯指引而不破壞 validator。
- 與 macOS 系統 Bash 3.2 相容 (沒有 associative array、沒有 `readarray`)。

### `scripts/promote-todo.sh`

把 `P1` / `P2` / `P3` / `P?` 的 active 條目搬到 `## Done`，使用日期化
的 `Done` 語法，並重新驗證。

```sh
scripts/promote-todo.sh \
  --title "<substring of the item's title>" \
  --summary "<one-line shipped summary>"
```

行為：

- 對標題欄位做 substring 匹配 (case-sensitive)。如果 0 個或多個 active
  條目匹配就拒絕跑 —— 把 substring 寫精準。
- 把新的 `Done` 條目插入 `## Done` heading 之後，使用
  `date -u +%Y-%m-%d` (用 `--date YYYY-MM-DD` 覆寫)。
- 在自身旁邊查找 validator；編輯後驗證失敗就還原原檔。
- 用 `--dry-run` 預覽改寫後的檔案而不改動。

### `scripts/init.sh`

詳見上面工作流程。值得注意的 flag：

- `--agent-contract FILE` —— 覆寫自動偵測的 `AGENTS.md` /
  `CLAUDE.md` / `.opencode/AGENTS.md` / `.cursorrules` 選擇。
- `--readme ""` —— 跳過 README 片段 (對於有自己慣例的 repo 有用)。
- `--no-validate` —— 跳過最後的 `todo-kanban.sh --validate-only`
  (給有獨立驗證步驟的 scripted bootstrap 用)。

## skill 按需載入的 reference 文件

- [`references/tag-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/tag-schema.md)
  (也有人類可讀的版本：[Tag schema](../reference/tag-schema.md))
- [`references/when-to-add-docs.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/when-to-add-docs.md)
- [`references/anti-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/anti-patterns.md)
- [`references/deployment-exclusion.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/deployment-exclusion.md)

## 這個 repo 怎麼把 skill 用在自己身上

repo 自己的 [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)、
[`backlog/`](../../backlog/) (有資料時)、[`pitfalls/`](../../pitfalls/)
(有資料時)、以及 [`scripts/`](../../scripts/) 中的 `todo-kanban.sh` /
`promote-todo.sh` 是 harness 套用在實際 project 上的活範例。
[`make kanban`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
target 包裝 validator/renderer。
