# pueue-job-queue

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

驅動 [Nukesor/pueue](https://github.com/Nukesor/pueue) —— 一個由 daemon
撐起來的 shell job queue —— 做佇列 (queued)、平行、排程、輕度 DAG 化的
shell 工作。這個 skill 是個 **CLI 橋接器**，**不是**自製排程器：它包裝
`pueue add --after`、`pueue status --json`、`pueue log --json`，讓 agent
可以提交、批次、串接、等待、重試，而不會搞丟正在跑的東西。

| 介面 | 它回答的問題 |
|---|---|
| `check-daemon.sh` | 「`pueued` 在跑嗎？這個 OS 上 log 在哪？」 |
| `submit.sh` | 「提交一個任務並給我可解析的 `{task_id, label, group, after}`。」 |
| `submit-dag.py` | 「把整條 fan-out / fan-in pipeline 提交、依賴接好 —— 在一個依 DAG 寬度開大小的、全新隔離的 group 中。」 |
| `wait.py` | 「Block 直到這些任務結束，並摘要成功 / 失敗。」 |
| `cleanup.sh` | 「回收 disk + status 延遲：清掉舊任務、空的 group、log 檔。」 |
| `references/cli-cheatsheet.md` | 「我該抓哪個沒被包裝的 `pueue` subcommand？」 |
| `references/json-schema.md` | 「`pueue status --json` 長什麼樣？QUERY DSL 語法是什麼？」 |
| `references/dag-patterns.md` | 「fan-out / fan-in / 菱形怎麼表達？」 |
| `references/daemon-and-config.md` | 「macOS / Linux 怎麼自動啟動 `pueued`？」 |

這個 skill 存在是為了讓 agent 不必煩三件事：

1. **記帳 (Bookkeeping)** —— task id、依賴接線、group 自動建立、
   `pueue add --print-task-id` 的 id 防禦性解析。
2. **Schema 漂移** —— `pueue status --json` 用 serde tagged enum
   (`{"Done": {"result": "Success" | "DependencyFailed" | "Killed" | {"Failed": <int>}}}`)。
   `wait.py` 分類所有變體，回傳可預測的 exit code (`0` ok、
   `5` 任何失敗、`6` timeout)。
3. **Footgun** —— `pueue add -- bash -c 'sleep 60'` **不會**保留內層
   引號 (pueue 會 re-shell)；`pueue kill --all` 也會暫停每個 group；
   `pueue restart` (預設) 建立**新的** id；`pueue clean` (預設) 也會
   清掉失敗。SKILL.md 有一份 10 條的 gotcha 清單涵蓋每一個。

## skill 觸發時機

- 「跑這 30 個指令，最多 4 個同時」→ 設 group 平行度，迴圈
  `submit.sh --group sweep`。
- 「啟動一個長訓練 job 然後我可以闔上筆電」→ `submit.sh
  -- ./train.sh` (pueue 跨 reboot 持久)。
- 「task B 只在 task A 成功後跑」→ `submit.sh --after $A_ID -- ./b.sh`。
- 「fan out 4 個訓練，再 evaluate」→ `submit-dag.py dag.yaml`。
- 「今晚排程跑這個」→ `submit.sh --delay 6h -- ./nightly.sh`。
- 使用者說 **pueue / pueued / pueue add / pueue queue / pueue group**
  或問「shell job 的 task queue」。

## 何時不該用

- 一個短的 shell 指令 —— 直接跑就好，pueue 帶 daemon 開銷。
- 跨主機排程、OR-deps、條件分支、retry-with-backoff、typed task IO
  —— 升級到 **Airflow / Prefect / Dagster / DVC / Slurm**。
  `references/dag-patterns.md` 有決策表。
- 長時間執行的 service —— 那是 `systemd` / `launchd` 的事。

## 結構

```
skills/local/pueue-job-queue/
├── SKILL.md                                  # ~275 行
├── scripts/
│   ├── check-daemon.sh                       # bash; daemon 健康 + auto-start
│   ├── submit.sh                             # bash; submit-one 包裝、JSON out、group 自動建立
│   ├── wait.py                               # PEP 723; block 直到終止狀態、state-change events、JSON 摘要
│   ├── submit-dag.py                         # PEP 723 (pyyaml); DAG submitter 含 --isolated-group / --auto-parallel
│   └── cleanup.sh                            # bash; 清 task + 空 group + 老 log 檔
├── references/
│   ├── cli-cheatsheet.md                     # 沒被包裝的指令
│   ├── json-schema.md                        # 觀察到的 status --json 形狀 (4.0.2) + QUERY DSL + jq 食譜
│   ├── dag-patterns.md                       # fan-out / fan-in / diamond + 升級表
│   └── daemon-and-config.md                  # 各 OS 的 pueued setup、config 旋鈕、log 路徑
├── assets/
│   ├── dag.example.yaml                      # 5-task fan-out / fan-in fixture
│   └── pueue.yml.example                     # config with `pause_group_on_failure: true`
└── tests/
    ├── conftest.py                           # 隔離的 pueued fixture，無 pueue 時 skip
    ├── test_submit.py                        # submit.sh 路徑 + 依賴失敗
    ├── test_dag.py                           # 拓撲 invariant、cycle/unknown/missing-cmd、isolated-group
    ├── test_wait.py                          # 成功/失敗/timeout exit code
    ├── test_contracts.sh                     # bash --help/error-code 契約
    └── fixtures/simple-dag.yaml              # 4-task diamond
```

## 永遠帶 label

`pueue status` 會把 **label** 欄位顯示在 command 之前。在繁忙佇列中，
掃 label 是一眼分辨多個 `train.py` run 的唯一方法。skill 的 gotcha 區段
的開頭就是：

> 提交時永遠帶 `--label`，且偏好能把這個 task 跟它的兄弟區分開的名字。

慣例：`<verb>-<subject>-<key>` (≤30 字元)。把區別 (seed、dataset slice、
model variant) 編進去 —— 不是命令本身：

| 好 | 壞 |
|---|---|
| `train-baseline-seed1` | `task1` |
| `eval-prod-2026q1` | `python eval.py --quarter 2026q1` |
| `nightly-featurize` (DAG) | `step-2-of-5` |

`submit-dag.py --label-prefix <run>-` 會產生 `<run>-<task_name>`，
這樣 `wait.py --label-prefix <run>-` 可以選整張圖、`pueue clean`
也可以稍後依此過濾。

## 經驗 schema (Empirical schema)

Pueue 的 JSON 輸出在 wiki 沒有正式文件化。skill 在
`references/json-schema.md` 出貨在 **pueue 4.0.2** 上觀察到的形狀，
含一個用來在不同主版本上重新驗證的診斷片段。關鍵形狀：

```json
{
  "tasks": {
    "<id>": {
      "id": 17,
      "label": "train-baseline-seed1",
      "group": "ml",
      "dependencies": [12, 14],
      "status": {
        "Done": {
          "enqueued_at": "...", "start": "...", "end": "...",
          "result": "Success"            // 或 "DependencyFailed" | "Killed" | {"Failed": 1}
        }
      }
    }
  },
  "groups": {
    "default": {"status": "Running", "parallel_tasks": 1}
  }
}
```

`wait.py` 分類每一種變體；如果未來 pueue release 新增一種（比方
`Suspended`），測試套件會在 skill 變得啞掉前抓到。

## 驗證 (Verification)

skill 出貨 **22 個 pytest 案例**，會在 tempdir-scoped config 底下啟動
隔離的 `pueued` —— 你的真實佇列永遠不會被碰到 —— 加上一個 bash
exit-code 契約測試。`pueue` / `pueued` 不在 `PATH` 時兩者都會自動 skip。
`lint-skill --strict` 是乾淨的 (0 error、0 warning)。

```bash
uv run --extra dev pytest skills/local/pueue-job-queue/tests/ -q
bash skills/local/pueue-job-queue/tests/test_contracts.sh
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/pueue-job-queue --strict
```

pytest fixture 在測試之間用 `pueue reset --force`，因為樸素的
`pueue kill --all` 也會暫停每個 group —— 一個值得文件化、非顯而易見的
失敗模式（詳見 SKILL.md gotcha）。
