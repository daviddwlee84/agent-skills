# long-running-jobs

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

決定 **agent 該怎麼等** 那些跨越單一回合 (turn) 的工作 —— 訓練、Slurm job、
sweep、長時間 build。這個 skill 之所以存在，是因為最直覺的作法剛好是最貴的。

## 它解決的問題

Agent 顧一個 8 小時的訓練時，通常會排一個定時回檢 (scheduled check-in)：
16:31 醒來、跑 `squeue`、看到「還在 epoch 21」、再排下一次。這行得通，而且是
所有選項裡最糟的一個。

> **Polling 本身不是問題。把 model 放進 polling 迴圈裡才是。**

```
until squeue -h -j "$JID" | grep -q .; do sleep 60; done   # 8 小時，~0 tokens
```
```
CronCreate -> 醒來 -> squeue -> 「還在 epoch 21」 -> 重排
                                # 每一次 tick 都要完整讀一次 context
```

兩者都在 polling。但在一個扛著 400k+ tokens 的 session 裡，只有其中一個會每
60 秒燒掉一整個 context window。這個 skill 的核心論點就是
**把計時器移出 context window** —— 移進 scheduler、移進被 block 住的 shell、
或是寫到磁碟上。

## 階梯 (the ladder)

挑**編號最小、且適用**的那一層。

| Tier | 機制 | 什麼時候用 |
|---|---|---|
| **0** | Scheduler 擁有整條鏈 (`sbatch --dependency=afterok`、`pueue --after`) | 有下一步。能撐過 session 死掉、context 壓縮 (compaction)、筆電睡眠。 |
| **1** | 一次 blocking 等待，丟背景 (`sbatch --wait`、`run-and-mark.sh`) | 你必須在完成時做反應。context 內零 polling。 |
| **2** | 串流經 shell 過濾後的事件 | 你必須在**跑到一半時**反應 —— OOM、early stopping、某個門檻。 |
| **3** | 定時回檢 | 最後手段：你握不到 handle 的遠端系統。 |

Tier 0 是最常被跳過的一層。它要求你在第一個 job 結束**之前**就知道下一個指令
—— 而只要你知道，agent 就被整個移出迴圈了。

## 不變式 (the invariant)

與四層都正交：**不管誰在等，總得有東西能在「沒人等」的情況下存活。**

```bash
python train.py; rc=$?
printf '%s\n' "$rc" > runs/v2.exit.tmp && mv runs/v2.exit.tmp runs/v2.exit
```

先寫暫存檔再 `mv`，在同一個 filesystem 內就是一次 `rename(2)`，所以讀的人只會
看到「沒有 marker」或「完整的 marker」—— 不會讀到寫到一半的 exit code 然後把
它當成成功。

由此推出的讀取規則：

| 觀察到 | 意思 |
|---|---|
| 有 marker、`0` | 成功 |
| 有 marker、非零 | 失敗 |
| 沒 marker、從未啟動 | 還沒開始 |
| **沒 marker、但啟動過** | **未知** —— 被砍了、node 掛了、**或還在跑** |

**「不存在」永遠不等於成功，也不等於失敗。** 把「未知」當成「還沒做完，所以重跑」
，就是你最後會有兩份同樣的八小時 job 的原因。

| 介面 | 它回答的問題 |
|---|---|
| `run-and-mark.sh` | 「跑這個、block 住、留下一筆能活過我這個 session 的紀錄。」 |
| `check-runs.sh` | 「我不在的時候，哪些跑完了？」 |
| [`references/claude-code-mechanisms.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/references/claude-code-mechanisms.md) | 「每一層對應到哪個 harness 工具？」 |
| [`references/scheduler-chaining.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/references/scheduler-chaining.md) | 「怎麼接 Phase A → Phase B，讓沒有任何東西需要保持清醒？」 |
| [`references/completion-contracts.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/references/completion-contracts.md) | 「怎麼記錄完成狀態，才能同時活過 queue 和 session？」 |
| [`assets/chained.sbatch.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/long-running-jobs/assets/chained.sbatch.template) | 「直接給我已經接對的 dependency 管線。」 |

## 兩個讓這個 skill 值得存在的事實

**丟背景執行的 shell 指令會在結束時叫醒 agent。** 這點是對 Claude Code 2.1.220
實測驗證的，harness 自己的 guidance 也這麼說：

> "Use the Monitor tool to stream events from a background process (each stdout
> line is a notification). For one-shot \"wait until done,\" use Bash with
> `run_in_background` instead."

這讓 Tier 1 變成單一一次呼叫，而不是一個迴圈。那些聲稱 agent 必須自己輪詢才能
知道完成的公開文件摘要**已經過時**；skill 裡有明講這件事，因為照過時版本做，
就等於把這個 skill 想消滅的 polling 又加回來。

**Slurm 的 parent 失敗時，child 會永遠卡在 pending。** 出自 `sbatch(1)`：

> "By default the job stays pending with reason DependencyNeverSatisfied"

> "Once a job dependency fails due to the termination state of a preceding job,
> the dependent job will never be run, even if the preceding job is requeued"

所以 Phase A 失敗時 Phase B **不會跟著失敗** —— 它會無限期停在那，在 `squeue`
裡看起來跟「排隊等資源」一模一樣，而且把 Phase A 修好重新 requeue **也放不出
它**。因此 skill 裡每一條鏈都帶著 `--kill-on-invalid-dep=yes` 和
`--mail-type=INVALID_DEPEND`。這個坑有自己的
[pitfall 頁面](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/slurm-dependent-job-pends-forever-after-failed-parent.md)。

## 什麼時候會觸發

- 某個 job「要跑好幾個小時」/「跑整晚」/「明天早上才會好」。
- 「跑完再回來跟我說」、「等訓練跑完」、「A 跑完之後接著跑 B」。
- **你正打算排一個週期性回檢，或重複跑 `squeue` / `nvidia-smi` /
  `ls checkpoints/` 來看某個東西好了沒。** 這個衝動本身就是觸發條件。

## 什麼時候不該用

- 幾秒就跑完的指令 —— 直接跑就好。
- Metrics、曲線、參數追蹤 → `mlflow-tracking`。
- 記錄這次跑的**意義** → `experiment-knowledge-harness`。
- 資源請求與 GPU 隔離 → `slurm-hpc`。

## 結構

```
skills/local/long-running-jobs/
├── SKILL.md                                # 階梯、不變式、8 個 gotcha
├── scripts/
│   ├── run-and-mark.sh                     # bash 3.2；把指令當自己的 child、block、原子性 marker
│   └── check-runs.sh                       # bash 3.2；marker 讀取器，exit 0/3/4
├── references/
│   ├── claude-code-mechanisms.md           # 每層對應工具；被擋掉的前景 sleep；cron 限制
│   ├── scheduler-chaining.md               # Slurm dependency 矩陣與陷阱；pueue；DVC
│   └── completion-contracts.md             # 原子性 marker；sacct 狀態；等待原語的可攜性
└── assets/
    └── chained.sbatch.template             # Phase A/B 鏈，預設就是對的
```

## 要嘛擁有那個 process，要嘛擁有一個 marker

`completion-contracts.md` 裡的可攜性表格導出一個值得特別點名的設計決定：

| 原語 (primitive) | 可用平台 |
|---|---|
| `wait "$PID"` | 到處都能用 —— 但**只能等目前 shell 的 child** |
| `tail --pid=PID` | 只有 GNU coreutils；BSD/macOS 的 `tail` 直接拒絕 |
| `pidwait` | Linux (procps-ng) |
| `inotifywait` | Linux；若 marker 早於監看啟動就會 **race** |
| `flock` / `fswatch` | 原生 macOS 沒有 |

**沒有任何可攜的方式可以等一個「別人的」PID。** 所以 `run-and-mark.sh` 把指令
當成自己的 child 來跑，這樣到處都有的 `wait` 就夠用了。

## 驗證

Skill 裡的每個主張都是實測而非臆測：

```bash
bash skills/local/skill-author/scripts/lint-skill.sh --strict skills/local/long-running-jobs

# exit code 契約，在原生 macOS bash 3.2 下
/bin/bash scripts/run-and-mark.sh --marker-dir .r --name ok  -- /bin/sh -c 'exit 0'   # 0
/bin/bash scripts/run-and-mark.sh --marker-dir .r --name oom -- /bin/sh -c 'kill -9 $$'  # 137
/bin/bash scripts/check-runs.sh --marker-dir .r --json | python3 -m json.tool
```

- 把 `run-and-mark.sh` 丟背景會觸發**真實的**完成通知，並帶著指令的 exit code
  —— Tier 1 機制的端到端驗證。
- `SIGKILL` 被保留成 **137**，所以 OOM 跟 `exit 1` 分得出來 —— 這是
  `sbatch --wait` 單獨做不到的（它把所有 signal 死法都壓成 `1`）。
- 用假的 `sbatch` 吐出 `999;clus`，結果得到 `--dependency=afterok:999`，
  驗證了 `${JID%%;*}` 這個 cluster 後綴的剝除。
- `check-runs.sh` 的「未知」回傳 `4`，排在「失敗」的 `3` **前面** ——
  因為未知才是需要人來判斷的狀態。
