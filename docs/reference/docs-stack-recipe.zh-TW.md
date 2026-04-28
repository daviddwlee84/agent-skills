# Downstream docs stack recipe — 下游 docs 技術組合配方

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

> 這頁現在由 `mkdocs-site-bootstrap` skill 維護。
>
> 完整配方在該 skill 的 reference 檔案：
> [`skills/local/mkdocs-site-bootstrap/references/docs-stack-recipe.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/docs-stack-recipe.md)
>
> 該 skill 也綁了現成可複製的 template 給 `mkdocs.yml`、
> `pyproject.toml`、GitHub Actions workflow，跟 docs 骨架 (skeleton) ——
> 詳見該 skill 的 [`assets/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/mkdocs-site-bootstrap/assets)
> 目錄。

## 快速開始 (Quick start)

如果你的 project 還沒用 `mkdocs-site-bootstrap`，套用同樣 docs 技術組合
的最簡單方式是在你的 repo 中調用該 skill：

```bash
# 在你 project 的 repo 根目錄
bash <path-to-agent-skills>/skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/
```

接著啟用 GitHub Pages 並觸發第一次部署 (deploy)：

```bash
bash <path-to-agent-skills>/skills/local/mkdocs-site-bootstrap/scripts/enable-pages.sh \
  --repo owner/repo
```

關於這個技術組合實際包含什麼 (Material theme + mkdocs-llmstxt +
mkdocs-copy-to-llm + pymdownx.snippets)、strict mode 強制的連結規則、
以及 GitHub Actions workflow 的接線方式，請讀上面連結的 canonical
reference。

## 另見 (See also)

- [Skill 頁面: mkdocs-site-bootstrap](../skills/mkdocs-site-bootstrap.md) ——
  完整 skill 工作流程的詳細導覽，包含 consent gate、preferences、
  以及既有 docs 處理。
- [Conventions](../conventions.md#documentation) —— 套用在**這個** repo
  的 `docs/` 樹的特定規則。
