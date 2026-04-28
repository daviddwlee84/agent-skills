# TODO format — TODO 格式

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁文件化
[`scripts/todo-kanban.sh`](scripts.md#todo-kanbansh) 驗證的精確文法。
適用於這個 repo 自己的
[`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)
與任何跑過
[`project-knowledge-harness` 的 `init.sh`](../skills/project-knowledge-harness.md)
的 project。

## 檔案層級結構

1. 第一個非空 heading **必須**是 `# TODO`。
2. Section **必須**按此順序出現：
   `## P1`、`## P2`、`## P3`、`## P?`、`## Done`。
3. `## Done` 之後，允許再有額外的 `## ...` heading（例如 `## Notes`
   區段、prune 紀錄）。validator 會在那一刻停止檢查條目格式。
4. 任何**不是**頂層 `- [ ]` / `- ✅` 條目的東西 —— 散文段落、
   blockquote、HTML 註解、`---` 分隔線、縮排的 sub-bullet —— 都會
   被忽略。你可以在每個 section heading 底下寫內聯 (inline) 指引，
   不會破壞驗證。

## 條目層級文法

| Lane | 格式 |
|---|---|
| `P1` / `P2` / `P3` | `- [ ] **[Effort] Title** — description` |
| `P?` | `- [ ] **[?/Effort] Title** — description` |
| `Done` | `- ✅ [YYYY-MM-DD] [P#/Effort] Title — summary` |

其中：

- **Effort** 是 `S`、`M`、`L`、`XL` 之一。`P?` 條目若 effort 也未知，
  使用 `[?/?]`。
- **Title** 不能含 `*`（validator 用尾隨 `**` 當分隔符）。
- **Description / summary** em-dash (`—`，U+2014) 後可以是任意文字。
  普通連字號 (`-`) 不被接受。
- Active 條目可以以 ` → [research](backlog/<slug>.md)` 結尾，把索引
  條目連到 `backlog/` 文件。
- `Done` 條目使用 `YYYY-MM-DD` 格式日期。慣例採 UTC；promote script
  使用 `date -u +%Y-%m-%d`。

## 範例

```markdown
## P1

- [ ] **[S] Wire up GitHub Pages** — first deploy of the docs site

## P2

- [ ] **[L] Migrate kanban to Python** — Bash 3.2 compat is getting expensive → [research](backlog/kanban-python.md)

## P?

- [ ] **[?/M] Try Rspress for docs** — evaluate AI-native docs framework alternative
- [ ] **[?/?] Skill-set lint** — vague idea, needs scoping

## Done

- ✅ [2026-04-23] [P1/M] Restructure project-knowledge-harness — looser validator, init/promote scripts, references/ progressive disclosure
```

## 依賴此格式的工具

- [`scripts/todo-kanban.sh`](scripts.md#todo-kanbansh) —— validator 與
  Markdown / JSON 看板渲染器 (renderer)。
- [`scripts/promote-todo.sh`](scripts.md#promote-todosh) —— 從 active
  lane 原子性地搬到 `## Done`。
- [`scripts/add-todo.sh`](scripts.md#add-todosh) —— 結構化插入到對應
  lane。
- [`scripts/sweep-inbox.sh`](scripts.md#sweep-inboxsh) —— 透過反覆呼叫
  `add-todo.sh` 把 `backlog/inbox.md` 的零散捕獲形式化。

如果你發現自己想要這裡沒有的某種語法，值得問問新形狀是真的有用，
還是只是另一個偽裝過的 `IDEAS.md` —— 詳見
[`references/anti-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/references/anti-patterns.md)。
