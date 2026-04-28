# streamlit-to-marimo (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[marimo-team/skills/skills/streamlit-to-marimo](https://github.com/marimo-team/skills/tree/main/skills/streamlit-to-marimo)
vendor 過來。透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/streamlit-to-marimo/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/streamlit-to-marimo/SKILL.md)
—— 變更會在下次同步被蓋掉。

## Upstream frontmatter description

> Convert a Streamlit app to a marimo notebook.

## 教什麼 (What it teaches)

從 Streamlit 命令式 (imperative)、整個 script 重跑的模型，遷移到 marimo
反應式 (reactive) DAG 的 pattern。涵蓋 `st.session_state`、
`st.cache_data`、Streamlit widget 對應到 marimo 等價物的方式 ——
通常是 `mo.state`、`@functools.cache` 或 cell-level reactivity、
以及 `mo.ui.*`。

## 相關 local skill

- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) —— 如果 Streamlit
  app 同時當互動 UI 跟 script 用，轉換後的 marimo notebook 可以採用
  雙模式 pattern。

## Canonical SKILL.md

完整 migration checklist 見
[skills/vendor/streamlit-to-marimo/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/streamlit-to-marimo/SKILL.md)。
Upstream 來源：
[marimo-team/skills](https://github.com/marimo-team/skills)。
