# marimo-notebook (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[marimo-team/skills/skills/marimo-notebook](https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook)
vendor 過來。透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/marimo-notebook/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/marimo-notebook/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Write a marimo notebook in a Python file in the right format.

## 教什麼 (What it teaches)

通用 (general-purpose) marimo 撰寫慣例 —— cell、reactive 依賴、`.py`
notebook 檔案格式怎麼運作。任何時候使用者要從零寫 marimo 程式碼，
都該載入這個基礎 skill。

## 相關 local skill

- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) —— 雙模式 (dual-mode：
  UI + batch CLI) notebook 搭配 Tyro + MLflow，建立在這些撰寫慣例之上。

## Canonical SKILL.md

完整指示見
[skills/vendor/marimo-notebook/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/marimo-notebook/SKILL.md)。
Upstream 來源：
[marimo-team/skills](https://github.com/marimo-team/skills)。
