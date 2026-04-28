# anywidget (vendored)

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

從
[marimo-team/skills/skills/anywidget](https://github.com/marimo-team/skills/tree/main/skills/anywidget)
vendor 過來。透過 [`make sync`](https://github.com/daviddwlee84/agent-skills/blob/main/Makefile)
同步；不要在本機編輯
[`skills/vendor/anywidget/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/anywidget/SKILL.md)
—— 變更會在下次同步被蓋掉。

> **關於 runtime 名稱：** SKILL.md frontmatter 宣告
> `name: anywidget-generator`。Skill 發現使用 frontmatter name，
> 不是目錄名。目錄保留為 `anywidget/` 是為了鏡射 upstream 路徑。

## 教什麼 (What it teaches)

為 marimo notebook 產生 [anywidget](https://anywidget.dev/) component：

- `_esm` 用原生 JavaScript 寫一個 `render({ model, el })` function。
- `_css` 樣式同時支援淺色與深色模式（透過
  `@media (prefers-color-scheme: dark)`）。
- 用 `model.get` / `model.set` / `model.save_changes` 模式在
  Python (`traitlets.Int(0).tag(sync=True)`) 與 JS 之間同步狀態。
- 給 marimo 顯示用的包裝：`widget = mo.ui.anywidget(MyWidget())`。
- widget 變大時用 `pathlib` 從外部檔讀 `_esm` / `_css`。

## 快速範例 (Quick example)

```python
import anywidget
import traitlets
import marimo as mo

class CounterWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let count = () => model.get("number");
      let btn = document.createElement("button");
      btn.innerHTML = `count is ${count()}`;
      btn.addEventListener("click", () => {
        model.set("number", count() + 1);
        model.save_changes();
      });
      model.on("change:number", () => {
        btn.innerHTML = `count is ${count()}`;
      });
      el.appendChild(btn);
    }
    export default { render };
    """
    _css = "button { font-size: 14px; }"
    number = traitlets.Int(0).tag(sync=True)

widget = mo.ui.anywidget(CounterWidget())
widget
```

然後從另一個 cell，`widget.value["number"]` 給你目前的計數。

## 相關 skill

- [`marimo-notebook`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/marimo-notebook/SKILL.md)
  —— 通用 marimo 撰寫慣例（從 marimo-team vendor）。
- [`marimo-batch-mlflow`](marimo-batch-mlflow.md) —— 使用 `mlflow-widgets`
  （anywidget-based 的 MLflow component library）做即時訓練圖表；
  如果你需要建客製化變體，這個 skill 就是你會用到的。

## Canonical SKILL.md

完整觸發描述與 best-practices 區段見
[skills/vendor/anywidget/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/anywidget/SKILL.md)。
