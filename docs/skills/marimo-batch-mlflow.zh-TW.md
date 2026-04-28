# marimo-batch-mlflow

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

[marimo-team/skills/marimo-batch](https://github.com/marimo-team/skills/tree/main/skills/marimo-batch)
的有意見 (opinionated) fork，置換三件事：

| 關注點 | upstream `marimo-batch` | 這個 skill |
|---|---|---|
| CLI 解析 | `mo.cli_args()` + 手寫 `rich.Table` 做 `--help` | `tyro.cli(ModelParams)` —— 自動 `--help`、type coercion、validation |
| Param 模型 | Pydantic `BaseModel` | `dataclass` (主要) 或 `pydantic.BaseModel` (替代) |
| Tracking | Weights and Biases | MLflow (`mlflow` + 可選的 [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) 做即時圖表) |

當使用者已經在 (或樂於用) MLflow、且偏好 strongly-typed CLI 時用這個
skill。當使用者已經在 W&B 上時用 upstream。

## 出貨內容 (What ships)

- 完整 SKILL.md
  ([skills/local/marimo-batch-mlflow/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/SKILL.md))
  含跟 upstream 的決策矩陣、雙模式 pattern 配方、以及給 params /
  EnvConfig / training loop / live chart 的 cell-level template。
- 一份 reference notebook
  ([starting-point.py](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/references/starting-point.py))
  —— 完整 PyTorch 訓練 notebook，含 dataclass param、Tyro CLI、
  MLflow logging、以及在 script 模式下被 gate off 的即時 `MlflowChart`
  cell。
- Pydantic 變體片段
  ([params-pydantic.py](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/references/params-pydantic.py))
  —— 只有 params cell 不同；notebook 其餘部分相同。
- grid-search launcher
  ([grid.py](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/marimo-batch-mlflow/references/grid.py))
  —— 透過 Hugging Face Jobs 做隨機化 sweep，注入 MLflow secret。
  預設 dry-run；`--launch` 才實際 submit。

## 雙模式 pattern (the core idiom)

```python
import marimo as mo
import tyro

is_script_mode = mo.app_meta().mode == "script"

if is_script_mode:
    params = tyro.cli(ModelParams)        # CLI flag
else:
    mo.stop(form.value is None, mo.md("*Submit form to start.*"))
    params = ModelParams(**form.value)    # UI form

# 底下每個 cell 用 `params.epochs`、`params.batch_size`、...
# 不知道是哪個分支產生的。
```

同一份 notebook 既是快速迭代用的 UI、**又是** `uv run notebook.py
--epochs 50` batch job 的進入點。零程式碼複製。

## 為什麼是 fork 而不是 vendor

upstream 的 `marimo-batch` skill 對 W&B 跟 `mo.cli_args()` 有特定意見。
Vendor + patch 會在每次 sync 被蓋掉；在 `skills/local/` 中做 local fork
讓分歧 (divergence) 安全且顯式。SKILL.md 也 cross-reference upstream，
讓使用者選對變體。

## Cross-references

- Upstream [`marimo-batch`](https://github.com/marimo-team/skills/tree/main/skills/marimo-batch)
  —— W&B 變體；如果使用者已經在 W&B 上就選這個。
- [`marimo-notebook`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/marimo-notebook/SKILL.md)
  —— 通用 marimo 撰寫 pattern (從 marimo-team vendor)。
- [`anywidget-generator`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/anywidget/SKILL.md)
  —— 當 `mlflow-widgets` 涵蓋不到時，用來建客製化 live-chart widget
  (從 marimo-team vendor)。
- [`mlflow-widgets`](https://github.com/daviddwlee84/mlflow-widgets) ——
  `starting-point.py` 即時圖表 cell 中使用的、以 anywidget 為基礎的
  MLflow 圖表 / 表格 / parallel-coordinate component。
- [Tyro docs](https://brentyi.github.io/tyro/) —— CLI 生成 reference；
  支援 dataclass、Pydantic、attrs。
