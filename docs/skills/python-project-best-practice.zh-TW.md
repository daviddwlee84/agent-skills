# python-project-best-practice

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

一套給「人與 agent 共同開發」的 Python 專案基線，並提供兩個入口：**從零 scaffold
新專案**，或**盤點並現代化既有專案**。兩者共用同一套慣例。

貫穿全篇的取向：**每個操作都只有一個標準、可被發現、非互動式的指令**。這是讓
repo 可被 agent 操作的關鍵，而且剛好也讓人類用起來更舒服。

> 範圍聲明：本 skill 刻意**不重述**
> [`verifiable-surfaces`](verifiable-surfaces.zh-TW.md)（CLI surface 設計）、
> [`marimo-batch-mlflow`](marimo-batch-mlflow.zh-TW.md)（dual-mode notebook）、
> [`fastapi-ai-patterns`](fastapi-ai-patterns.zh-TW.md)（production FastAPI）、
> [`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.zh-TW.md)（文件站）。它只連過去，
> 補上那個沒人涵蓋的缺口：專案本身。

## 它主張的預設 (defaults)

| 面向 | 預設 | 為什麼不選另一個 |
|---|---|---|
| 環境 | `uv` + 提交 `uv.lock` + `.python-version` | poetry / pip-tools / conda 解決的範圍都更小；`uv.lock` 從不會限制你的使用者 |
| 目錄結構 | `src/<pkg>/` | flat layout 匯入的是原始碼目錄，因此少了 `__init__.py` 或 package data 仍會測試通過、卻在安裝端壞掉 |
| 開發相依 | PEP 735 `[dependency-groups]` | extra 會被**發布**出去；你的 test runner 不該出現在使用者的相依圖裡 |
| Lint + format | `ruff check` + `ruff format` | `ruff format` 本身就是 black 的重寫版 —— 兩個同時裝只會互相打架 |
| 型別檢查 (type checking) | `ty`（精確 pin），mypy 作為保守替代 | `ty` 還在 0.0.x：快到大家真的會跑，但也不穩到不能用 `>=` |
| CLI | Tyro，一個 subcommand 一個 frozen dataclass | 指令即資料 (commands as data)，測試不需要 argv 也不需要 subprocess |
| Shell 補全 | `--tyro-write-completion` | 內建；再接 shtab / argcomplete 是多餘的 |
| Logging | loguru 只在 entry point，library 程式碼用 stdlib | library 若呼叫 `loguru.logger.add()`，會劫持匯入它的那支程式的 logging |
| 設定 (config) | pydantic-settings，預設值 < `.env` < 環境變數 | 而且 `<tool> info` 會印出實際解析結果 |
| Task runner | `Justfile`（taskipy 另註） | `just` 不需要 Python，所以 `just setup` 能自己把 venv 建起來 |

## 出貨內容 (What ships)

- 完整 SKILL.md（[SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/SKILL.md)）—— 決策主幹、兩個 workflow，以及
  22 條 gotchas。
- **九份 references**，按需載入：
    - [`uv-and-pyproject.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/uv-and-pyproject.md) —— 指令、
      groups vs extras、lockfile 政策、直譯器 pin、build backend、
      `uv tool install` / Trusted Publishing、workspaces。
    - [`tyro-cli.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/tyro-cli.md) —— dataclass 指令、subcommand
      union、模組拆分、補全、config object。
    - [`quality-gates.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/quality-gates.md) —— ruff 規則選擇、
      `ty` vs mypy、pytest 佈局、coverage 該放哪、CI、pre-commit。
    - [`logging-and-config.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/logging-and-config.md) ——
      app/library 分層規則、loguru 三個陷阱、pydantic-settings、direnv。
    - [`notebooks-and-widgets.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/notebooks-and-widgets.md) ——
      notebook 放哪、dual mode、與 ruff 的衝突、把 anywidget 收進套件。
    - [`api-and-services.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/api-and-services.md) —— FastAPI
      stub 的邊界，以及 **skill vs MCP** 的判斷規則（通常兩者皆非：加一個
      subcommand 就好）。
    - [`rust-pyo3.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/rust-pyo3.md) —— maturin 佈局、abi3、
      stale binary 陷阱、為何 type checker 需要手寫 `.pyi`。
    - [`agent-interface.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/agent-interface.md) —— AGENTS.md /
      README / 套件自帶 skill 的分工、symlink 規則、docs-drift gate。
    - [`legacy-refactor.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/references/legacy-refactor.md) —— 遷移階梯、
      一個 PR 一階、以及**哪些不該遷**。
- **兩支 PEP 723 script**（`uv run`、inline deps、stdout 出 JSON）：
    - [`new-python-project.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/scripts/new-python-project.py) —— 從內建
      template tree scaffold。`--profile {minimal,cli,lib,api,ml,rust}`、
      `--dry-run`、`--force`、`--no-git`。離線執行，不寫任何目標目錄之外的檔案。
    - [`audit-python-project.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/scripts/audit-python-project.py) ——
      26 項唯讀檢查，每項附證據與修法，並產出排序過的 `migration_plan[]`。
      `--format {json,table}`、`--fail-on {fail,warn,never}`。刻意**不提供
      `--fix`**。
- **一棵 template tree**（`assets/project/`，29 個 `.tmpl` 檔）加上
  [`assets/manifest.toml`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/python-project-best-practice/assets/manifest.toml)，標明每個目標路徑屬於哪些
  profile。不在 manifest 裡的檔案永遠不會被複製；manifest 與實際檔案兩邊只要對不
  上，generator 就以 exit 4 失敗。

## Profiles

疊加式設計，所以「之後再 agentic」現在不用付任何代價。

| Profile | 額外加入 |
|---|---|
| `minimal` | 套件、tests、Justfile、CI、AGENTS.md |
| `cli`（預設） | Tyro CLI、loguru、pydantic-settings、`[project.scripts]` |
| `lib` | 發布用 metadata、`py.typed` |
| `api` | 帶 `/docs` 與 `/openapi.json` 的 FastAPI app |
| `ml` | 同時可當 batch CLI 的 marimo notebook |
| `rust` | maturin backend、PyO3 crate、`.pyi` stubs |

## docs-drift gate

就算其他都不用，這一塊也值得抄走。關於 CLI 的敘述性文件，在有人改掉一個 flag
的那一刻就開始腐爛；所以生成的專案把它變成**建置產物**：

```bash
just docs-sync     # 從 --help 重新產生 AGENTS.md 與 .agents/skills/ 裡的 CLI 區塊
just docs-check    # 已提交的區塊過期就 exit 1 —— 已納入 `just check`
```

`scripts/sync_agent_docs.py` 會跑 `python -m <pkg>.cli --help` 與每個
subcommand 的 `--help`，去掉 ANSI，再貼回 `<!-- BEGIN CLI -->` 標記之間。因為
`--check` 同時在本地 gate 與 CI 裡跑，改了 flag 卻沒更新文件會直接讓 build 失敗。

## 經過驗證，不是宣稱

六個 profile 出貨前都實際生成並跑過：`uv sync` → `just check`（ruff format、
ruff lint、`ty`、pytest、docs-drift）六個全綠，coverage 介於 89% 到 100%，並且
完整跑過 `uv tool install` → 執行 → uninstall。有兩個說法因為實測而被改掉：

- **Tyro 本來就內建 shell 補全。** 初稿叫你去接 shtab，其實不必ーー
  `--tyro-write-completion {bash,zsh,tcsh,fish} PATH` 是內建的，而
  `--tyro-print-completion` 已被 deprecate，因為一個誤植的 `print()` 就會污染輸出。
- **`uv sync` 會默默留著過期的 Rust binary。** 改了 `rust/src/lib.rs` 再跑
  `uv sync`，舊的 `.so` 原封不動且毫無警告 —— 連你剛加的 debug print 也不會出現。
  實驗確認；解法是 `uv sync --reinstall-package <slug>`。

## 相關 skills

[`verifiable-surfaces`](verifiable-surfaces.zh-TW.md) ·
[`project-knowledge-harness`](project-knowledge-harness.zh-TW.md) ·
[`agent-history-hygiene`](agent-history-hygiene.zh-TW.md) ·
[`mkdocs-site-bootstrap`](mkdocs-site-bootstrap.zh-TW.md) ·
[`git-workflow`](git-workflow.zh-TW.md) ·
[`marimo-batch-mlflow`](marimo-batch-mlflow.zh-TW.md) ·
[`fastapi-ai-patterns`](fastapi-ai-patterns.zh-TW.md) ·
`cli-release-distribution`
