# Getting Started — 快速開始

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

## 安裝 skill

--8<-- "_snippets/install.md"

這會把這個 repo 中 `skills/local/` 與 `skills/vendor/` 底下的東西，
全部安裝到你 project 的 `.agents/skills/`。

## 渲染 (render) repo 自己的 backlog

如果你想看這個 repo TODO 清單的看板 (kanban) 視圖：

```bash
git clone https://github.com/daviddwlee84/agent-skills
cd agent-skills
make kanban
```

`make kanban` 會跑 [`scripts/todo-kanban.sh`](reference/scripts.md#todo-kanbansh)，
驗證 [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)
並印出依 lane 分組的 Markdown 看板。

## 在本機建構 docs

你正在讀的這個 docs 站是個
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 站。
本機預覽：

```bash
# 在 repo 根目錄
uv sync --extra docs
uv run mkdocs serve
```

然後打開 <http://127.0.0.1:8000/>。

要產生靜態站 (GitHub Pages 服務的就是這個產物)：

```bash
uv run mkdocs build
```

`make docs-serve` 跟 `make docs-build` 是這兩個指令的便利包裝。

## 把 project-knowledge-harness skill 套到你自己的 project

如果你只想要把 TODO + backlog + pitfalls 的結構帶到另一個 repo，
內建的 init script 一行搞定：

```bash
git clone https://github.com/daviddwlee84/agent-skills /tmp/agent-skills
/tmp/agent-skills/skills/local/project-knowledge-harness/scripts/init.sh \
  --target /path/to/your/project \
  --project-name "Your Project" \
  --deployment chezmoi   # 或 npm | pip | docker | none
```

script 做了什麼、支援哪些 flag，請看
[`project-knowledge-harness` 頁面](skills/project-knowledge-harness.md)。
