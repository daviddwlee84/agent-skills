# Agent skill compatibility — agent skill 相容性

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁記錄本 repo 對 `SKILL.md` 採用的跨 coding agent 相容性規則。
目標是實用 portability，不是把每個產品的專屬 extension 都混進 local skill。

## 我們採用的 baseline

Portable baseline 以
[Agent Skills specification](https://agentskills.io/specification) 為準：

| 欄位 | Repo policy |
|---|---|
| `name` | 必填，1-64 字元，小寫英數字與單一 hyphen 分隔，不可開頭/結尾 hyphen，不可 `--`，應與 skill directory 相同 |
| `description` | 必填，1-1024 字元，同時描述 skill 做什麼、何時使用 |
| `SKILL.md` body | 控制在約 500 行以內；長篇內容移到 `references/` |
| Optional frontmatter | 只有目標 agent 需要時才加；local skill 預設保持 portable |

`skill-author` 使用的 description budget tiers：

| Tier | 長度 | 意義 |
|---|---:|---|
| Green | 120-500 chars | Local skill 首選：有足夠 trigger surface，又不污染 context |
| Yellow | 501-900 chars | 合法，但偏重；細節應移到 body 或 references |
| Orange | 901-1024 chars | 合法，但接近 loader hard limit |
| Red | >1024 chars | Codex/Cursor/spec-aligned validator 會視為 invalid |

另外，前 60 個字元要有資訊量。`npx skills` installer 的 picker hint 只顯示
description 前 60 chars；Codex 在 skill 很多時也可能先縮短 description。

## 各 coding agent notes

| Tool | Preference / constraint | Link |
|---|---|---|
| Agent Skills spec | 定義 portable directory layout、frontmatter 欄位、64-char `name`、1024-char `description`，以及 optional `scripts/`、`references/`、`assets/`。 | [Specification](https://agentskills.io/specification) |
| Codex | 一開始只放每個 skill 的 name、description、path；選中後才載入完整 `SKILL.md`。初始 skill list 有 context budget，所以 description 要精簡、前置關鍵 trigger。Codex 可用 optional `agents/openai.yaml` 做 UI metadata 與 invocation policy。 | [Codex skills docs](https://developers.openai.com/codex/skills/create-skill) |
| Claude Code | 遵循 open standard，並增加 `when_to_use`、`disable-model-invocation`、`user-invocable`、`allowed-tools`、`context`、`hooks` 等欄位。Skill listing 會把 `description`/`when_to_use` 合併文字截到 1,536 chars。 | [Claude Code skills docs](https://code.claude.com/docs/en/skills) |
| Cursor | 使用 `SKILL.md` skills；其 managed `create-skill` guidance 採用同樣實務上的 64-char `name`、1024-char `description` budget。也支援 `disable-model-invocation` 作為 explicit-only skill。 | [Cursor skills docs](https://cursor.com/docs/skills) |
| OpenCode | 讀 `.opencode/skills`、`.claude/skills`、`.agents/skills`；只認特定 frontmatter 欄位，unknown fields 會被忽略。Enforce 1-64 char names 與 1-1024 char descriptions。 | [OpenCode Agent Skills](https://opencode.ai/docs/skills/) |
| `npx skills` | Installer/distributor。從 `SKILL.md` 讀 `name` 與 `description`，picker 只顯示 60-char description hint，並用 `.claude-plugin/marketplace.json` 分組。 | [npx skills metadata model](npx-skills-metadata.md) |

## 這個 repo 怎麼落地

- Local skill 的 `description` 預設應留在 green tier，除非有明確 trigger
  coverage 理由才加長。
- `skills/local/skill-author/scripts/lint-skill.sh` enforce portable hard
  limits：hyphen-case names、64-char names、1024-char descriptions。Yellow/orange
  tier 只印 note，不讓 strict mode fail。
- `skills/local/skill-author/assets/SKILL.md.template` 要求新 skill 目標
  120-500 chars，且絕不超過 1024。
- 詳細 trigger examples 應放在 `SKILL.md` body 或 `references/`，不要塞成超長
  frontmatter description。
- 產品專屬 metadata 可以用，但要 deliberate：local skill 優先 portable
  frontmatter；vendored upstream metadata 保持原樣；target-agent-only 欄位應在
  skill body 內說明。

## 促成這條 policy 的事件

`mkdocs-site-bootstrap` 曾有 1106-character frontmatter `description`。
Codex 0.128.0 因為 description 超過 1024 characters，直接把該 skill 判為
invalid 並跳過載入。這次把 description 縮到 489 chars，並更新
`skill-author`，讓未來 local skills 在 install/load 前就被 linter 擋下。
