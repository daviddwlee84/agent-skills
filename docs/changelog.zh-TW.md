# Changelog

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁摘要值得標註的變更。每天的 commit 歷史在
[git log](https://github.com/daviddwlee84/agent-skills/commits/main)；
這個檔案只挑里程碑 (milestone)。

## Unreleased

- 用 `mkdocs-llmstxt` 跟 `mkdocs-copy-to-llm` 啟動了一個
  [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) docs 站，
  可部署到 GitHub Pages。
- 新增 `scripts/add-todo.sh` 用來結構化插入 TODO，以及
  `scripts/sweep-inbox.sh` 把 `backlog/inbox.md` 的零散捕獲做分流
  (triage)。詳見 [Project memory workflow](workflows/project-memory.md)。
- 新增 [Downstream docs stack recipe](reference/docs-stack-recipe.md)，
  讓使用我們 skill 的 project 可以鏡射同樣的 docs setup。
- 新增 zh-TW 雙語 docs 支援（透過 `mkdocs-static-i18n`），保留
  「中文 (English original)」術語慣例。

## 2026-04 — `project-knowledge-harness` 結構整理

- 放寬 `scripts/todo-kanban.sh` 的 validator，會略過散文 (prose)、
  blockquote、HTML 註解、`---` 分隔線、以及縮排的 sub-bullet。
  新增 `--validate-only` 跟 `--json` flag。允許 `## Done` 之後再有額外
  的 `## ...` heading。
- 新增 `scripts/init.sh`，可以一行把 `TODO.md` + `backlog/` +
  `pitfalls/` + agent 指引 + README 片段一次設置到任何目標 repo。
- 新增 `scripts/promote-todo.sh`，原子性地把 active 條目搬到 Done，
  並重新驗證、支援 dry-run。
- 把 `SKILL.md` 瘦身（~350 → ~170 行），細節推到
  `references/{tag-schema,when-to-add-docs,anti-patterns,deployment-exclusion}.md`，
  做[漸進式揭露 (progressive disclosure)](https://agentskills.io/specification#progressive-disclosure)。

## 2026-03 與更早

- 最早的 vendor 系統 (`vendor.yaml`、`scripts/add-vendor.sh`、
  `scripts/sync-vendor.sh`、`make sync` / `make sync-check`)。
- 最早的 `project-knowledge-harness` skill（前身為 `backlog-harness`）。
- `quantatitive-factor-researcher` persona skill。
