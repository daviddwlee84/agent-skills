# skill-author

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

**新 agent skill** 的撰寫輔助。出貨：

- 一個 scaffolder
  ([`new-skill.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/scripts/new-skill.sh))
  建立 `skills/local/<name>/` 並預先填入標準佈局。
- 一個 linter
  ([`lint-skill.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/scripts/lint-skill.sh))
  檢查 frontmatter、script 衛生、reference 可達性，並 enforce 這個 repo 對
  `name` / `description` 採用的 portable agent-skill compatibility budget。
- 兩份濃縮 agentskills.io 指南的 reference：
  [authoring-patterns.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/references/authoring-patterns.md)
  與 [script-design.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/references/script-design.md)。
- 一份 repo-specific 慣例 reference
  ([this-repo-conventions.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/references/this-repo-conventions.md))
  說明佈局、鏡射、bash 3.2 相容性。
- SKILL.md、reference 文件、bash script (含 `--help` / `--dry-run` /
  strict-mode 樣板)、Python script (含 PEP 723 inline deps) 的 template。

## 跨 agent 相容性

這個 repo 的 local skills 會盡量保持可攜，能被 Codex、Claude Code、Cursor、
OpenCode 與 `npx skills` installs 正常使用。簡版規則：

- `name`：hyphen-case，<=64 chars。
- `description`：必填，<=1024 chars；首選 120-500 chars。
- Description 前 60 chars 要能在 picker UI 中提供有用資訊。
- Product-specific frontmatter 只有 deliberate 時才加。

完整 tool preferences、限制、來源連結，以及本 repo 的 tier policy 見
[Agent skill compatibility](../reference/agent-skill-compatibility.md)。

## 何時用這個 vs `skill-creator`

| 任務 | 用 |
|---|---|
| 「我想做一個給 X 用的新 skill」 | **skill-author** |
| 起手 SKILL.md / reference / script | **skill-author** |
| Lint 一份草稿 skill | **skill-author** |
| Skill 在預期時沒觸發 | `skill-creator` (description 優化) |
| 跑測試案例 / benchmark 一個 skill | `skill-creator` (eval 迴圈) |

兩者都適用時，先 `skill-author`，等結構對了再交棒給 `skill-creator`。

## 快速開始

```bash
# 1. Scaffold
bash skills/local/skill-author/scripts/new-skill.sh my-skill

# 2. 編輯 skills/local/my-skill/SKILL.md，填入 description 與 workflow

# 3. Lint
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/my-skill

# 4. (可選) 交棒給 skill-creator 做量化驗證
```

## 為什麼是分開的 skill？

`skill-creator`（Anthropic 出版、打包在 `.agents/skills/` 的那個）是 skill
創建的 canonical 權威，但它重點放在 **eval/iterate 迴圈**：spawn subagent、
評分、benchmark、優化 description 觸發率。`skill-author` 涵蓋
agentskills.io best-practices 與 using-scripts 頁面文件化的**撰寫 pattern**
—— gotchas 區段、output template、validation loop、calibrated specificity、
agentic CLI 設計 —— 加上 repo-specific 慣例與可運作的 scaffolder/linter
script。

兩者互補，互相顯式 cross-reference。

## Canonical SKILL.md

完整觸發描述與工作流程見
[skills/local/skill-author/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/skill-author/SKILL.md)。
