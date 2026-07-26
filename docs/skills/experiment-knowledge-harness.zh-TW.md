# experiment-knowledge-harness

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

給 ML / DL / Quant 專案用的、以檔案為基礎的**研究記憶 (research memory)**。
它是 `project-knowledge-harness` 的姊妹 skill：那個記的是**工程工作**，
這個記的是**我們相信什麼、以及為什麼**。

它要解決的問題：一個研究專案做了半年之後，沒人答得出「這個我們是不是試過了？」
—— 於是死路被重跑一次，GPU 時數被花第二遍。

| 介面 | 它回答的問題 |
|---|---|
| `experiments/LEDGER.md` | 「我們目前相信什麼？證據是什麼？」 |
| `experiments/ROADMAP.md` | 「接下來值得跑什麼？為什麼是這個順序？」 |
| `experiments/INBOX.md` | 「半夜兩點想到的原始點子丟哪？」 |
| `<NNN>-<slug>/REPORT.md` | 「到底跑了什麼？在什麼 spec 下？結果如何？」 |
| `experiments/README.md` | 自動渲染的 Mermaid 地圖 + 全部索引 |

## 讓它成立的兩個想法

**Findings 有編號、而且可被推翻。** 一則 finding 是 `F-007`，有日期、綁定產出
它的實驗、附證據連結。當後來的實驗與它矛盾時，
`log-finding.py --overturns F-007` 會把舊的移到墓園分區並加上刪除線 ——
歷史保持可讀，而不是被悄悄改掉。

**推翻一則 finding 會重新分流整個佇列。** ROADMAP 項目帶著
`depends-on: F-007`。當 `F-007` 倒下時，`retriage.py` 會列出所有靠它成立的計畫
實驗並以非零 exit code 結束。那些「因為某個你已不再相信的信念」才被排進去的
工作會被標記出來，而不是默默被執行。

## 預先登記 (pre-registration) 與單軸契約

每份 REPORT 都在**執行前**填好：

- **Pre-registration** —— 假說、成功判準、決策規則 (decision rule)。
  **如果決策規則的各個分支結果一樣，那就別跑這個實驗。**
  （光是這一項檢查就砍掉意外地多的實驗。）
- **單一消融軸 (one ablation axis)**，寫在 front-matter，對照一個**具名的**
  baseline。
- **可比較性 spec** —— 每張結果表都標明它是在哪個 `spec:`（成本模型、費率、
  評估視窗版本）下產生的。**不同 spec 的數字永遠不共用一張表。**

[`references/anti-patterns.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/experiment-knowledge-harness/references/anti-patterns.md) 點名了這些設計在防的失敗模式：HARKing、
沒有決策的實驗、winner's curse、spec 漂移、以及沒被寫下來的死路。

## 長時間執行期間

這個 harness 原本涵蓋執行**之前**（預先登記、分流）與**之後**（結論、findings、
provenance）。現在**執行期間**這段視窗也涵蓋了，因為 `status: running` 只是寫給
自己看的註記，沒有任何東西在盯著它：

1. **執行過程要寫下持久的完成 marker** —— 一個原子性的 exit code 檔案，讓
   **之後**的 session 能分辨「跑完了，exit 0」和「凌晨三點被砍了」，而不必重燒
   GPU 時數。重啟之後，把每一份 `status: running` 的 REPORT 拿去跟實際 marker
   對帳，而不是直接假設它還在跑。
2. **如果下一個實驗已經定了，就把它接在 scheduler 裡。** `depends-on: #NNN`
   標籤是文件 —— 它不排程任何東西。當 #008 真的要接在 #007 之後跑，就在同一時間
   用真正的 dependency 提交它。

明確**不建議**的作法：用一個會自我重排的定時回檢去顧一個長時間執行 —— 醒來、
grep log、發現沒變、再重排。詳見
[`long-running-jobs`](long-running-jobs.zh-TW.md)。

## 什麼時候會觸發

- 「這個我們是不是試過了？」/「別重複造輪子、別浪費算力」
- 記錄哪些方向成功、哪些失敗，讓死路維持是死路。
- 讓結果在數個月的跨度上仍可被發現、可被比較。
- 當某個結論改變時，重新排序既有計畫。
- 「給我所有實驗的大局圖。」
- 隨手記一個原始研究點子，或清一清 experiments inbox。

## 什麼時候不該用

- 單次的臨時計算 —— 沒有假說，就不是實驗。
- 沒有假說的工程工作 → `TODO.md` / `project-knowledge-harness`。
- **Run 層級的 metric 串流** → 那是 MLflow / W&B 的地盤。這個 harness 存的是
  結論與參照，不是原始的 run telemetry。

## 結構

```
skills/local/experiment-knowledge-harness/
├── SKILL.md
├── scripts/
│   ├── init.sh                     # 冪等地把骨架建進目標 repo
│   ├── new-experiment.py           # 配號 #NNN、產生 REPORT.md
│   ├── log-finding.py              # 追加 F-NNN；--overturns 移走舊的
│   ├── render-index.py             # 驗證所有介面 + 重寫 Mermaid 地圖
│   ├── sweep-inbox.py              # 把 INBOX 條目分流成 ROADMAP 項目
│   ├── retriage.py                 # 標出靠被推翻 finding 成立的項目
│   ├── snapshot-provenance.py      # 收集 git SHA、版本、主機、時間戳
│   └── _lib.py                     # 共用的純標準庫 parser / validator
├── references/                     # report-format、ledger-format、tag-schema、
│                                   # provenance、when-to-log-what、anti-patterns
└── assets/                         # 6 個模板，含 agent-guidance 片段
```

全部只用標準庫 Python + bash 3.2 —— 刻意保持 harness 無關 (harness-agnostic)，
所以在 Claude Code、Cursor、Codex 或純人工操作下表現一致。

## 可重現性階梯

[`references/provenance.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/experiment-knowledge-harness/references/provenance.md) 把 provenance 分級，而不是要求一步到位的完美：

| 級別 | 意思 |
|---|---|
| Anecdote | 訊息裡的一個數字 |
| Recorded | 數字 + 有標 spec 的 REPORT |
| Replayable | + git SHA、config hash、資料視窗、seeds |
| Pinned | + 環境與 artifact 路徑 |

**預設假設是沒有 tracking server。** 當 run telemetry 值得留存時，它建議用本機
SQLite 的 MLflow backend，讓整個儲存維持成單一可攜檔案。

## 驗證

`render-index.py` 是把關者：它依 status enum 驗證 REPORT front-matter、檢查
ledger 語法與交互參照、驗證 ROADMAP 項目文法（`payoff:` 與 `cat:` 為必填）、
標出缺少 REPORT.md 的實驗資料夾 —— 然後重寫地圖。`retriage.py` 在需要重新分流時
以 `1` 結束，因此可以掛進 CI。
