# skill-creator (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[anthropics/skills/skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
vendor 過來。透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/skill-creator/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/skill-creator/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Create new skills, modify and improve existing skills, and measure
> skill performance. Use when users want to create a skill from scratch,
> edit, or optimize an existing skill, run evals to test a skill,
> benchmark skill performance with variance analysis, or optimize a
> skill's description for better triggering accuracy.

## 教什麼 (What it teaches)

Anthropic 自己的 skill 撰寫方法論，包括：

- 評估 (evaluation) harness，量測 skill `description` 在應該觸發的
  prompt 上實際觸發的可靠度。
- 變異分析 (variance analysis) 的 benchmark（重複跑來區分真實的提升
  與雜訊）。
- 優化 (optimization) 迴圈，迭代 `description` 欄位直到觸發率達標。

## `skill-creator` vs local `skill-author`

| 面向 | `skill-creator` (vendored，這個) | [`skill-author`](skill-author.md) (local) |
|---|---|---|
| 焦點 | **評估** —— 測試案例、觸發率 benchmark、變異 | **撰寫** —— 起手、lint、agentskills.io best practices |
| Script | Eval harness、benchmark | `new-skill.sh`、`lint-skill.sh` |
| 何時使用 | 撰寫後，量測與優化 | 撰寫 SKILL.md + references + scripts 期間 |

兩者互補 —— 用 `skill-author` 建出 skill，再用 `skill-creator`
評估與調校它的觸發描述。

## Canonical SKILL.md

完整指示見
[skills/vendor/skill-creator/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/skill-creator/SKILL.md)。
Upstream 來源：
[anthropics/skills](https://github.com/anthropics/skills)。
