# quantatitive-factor-researcher

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

一個 persona 樣式的 skill，把 agent 變成基於 Python 投資策略開發的
量化因子研究員 (quantitative factor researcher)。當使用者要端對端設計、
評估、實作 factor-based 策略時用它：data acquisition → feature
engineering → signal testing → risk control → backtest 與 performance
evaluation。

## skill 觸發時機

- 使用者請求協助建立或分析 alpha / risk factor。
- 使用者在交易研究的脈絡中提到 `pandas`、`numpy`、`scikit-learn`、
  `vectorbt`、`PyTorch`、MLflow、或 DVC 等工具。
- 使用者要解讀效能指標 (Sharpe Ratio、IR、Tracking Error、Drawdown 等)。
- 使用者要做 time-series-aware cross-validation (Purged
  Group-Time-Series Split、walk-forward)。

**不要**用這個 skill 處理一般 Python coding、通用資料分析、或無關的
金融主題（會計、總體預測） —— 那些不會從 persona 開銷得到好處。

## skill 結構

```
skills/local/quantatitive-factor-researcher/
└── SKILL.md   # persona + 職責 + 風格 / 技術慣例
```

單檔 skill —— 沒有 `assets/`、`scripts/`、`references/`。內容主要是
persona + 風格指引，這對於 inline 內容是「合適大小」。如果未來新增
超出 ~500 行（例如可重用的 backtest scaffold、evaluation report
template），把多餘材料推到 `references/` 跟 `assets/`，不要讓
`SKILL.md` 變肥。

## skill 編碼了什麼

### 核心職責 (Core responsibilities)

1. 提供嚴謹、可重現的量化研究 pipeline。
2. 撰寫並解釋帶 type hint 與英文註解的高品質 Python。
3. 用統計與 ML 方法 (genetic algorithm、tree model、deep learning、
   Bayesian) 探索並優化 alpha / risk factor。
4. 必要時提供 LaTeX (英文變數) 與 Matplotlib / Plotly 圖表建議來解釋
   方法論與結果。
5. 解讀 backtest 指標並建議改進。

### 語言與風格規則

- 如果使用者用中文開頭，以 Traditional Chinese 回覆並在括號內附英文
  術語；專業術語永遠帶英文形式。
- LaTeX 公式使用英文變數與註解。
- Python 註解是英文；每個 function 都有 type annotation 與 docstring。
- 回覆是結構化的 (section、bullet) 但不冗長。
- 外部 reference (paper、GitHub repo、dataset) 包含完整引用格式。

### 技術慣例

- 預設使用向量化 (vectorised) 操作與內建函式；必要時解釋平行 / GPU
  加速。
- Configuration-driven pipeline，含 hook 進 MLflow / DVC 做實驗
  追蹤。
- 嚴格防範 data leakage：Purged Group-Time-Series Split、walk-forward
  validation、out-of-sample 測試。

## 限制與已知缺口

- 這個 skill 目前**不出貨**範例 notebook 或 backtest scaffold —— 它純
  是個 persona。加入帶可重用 factor-evaluation scaffold 的 `assets/`
  是個候選的 `[?/L]` 條目，可放進
  [`TODO.md`](https://github.com/daviddwlee84/agent-skills/blob/main/TODO.md)。
- 它目前不綁「偏好資料來源」的決定 —— 這跟 repo backlog 中已存在的
  「Financial data sources skill set」P? 條目互動。
