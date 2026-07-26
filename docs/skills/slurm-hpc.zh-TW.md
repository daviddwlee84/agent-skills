# slurm-hpc

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

適用於**任何** cluster 的可攜 Slurm 知識 —— 寫 `sbatch` script、挑資源請求、
串接 job、以及推理「到底什麼東西能隔離一個亂搞的 job」。刻意不綁特定站點
(site-agnostic)：某個 cluster 專屬的 partition 與慣例，以那個 repo 自己的
skill 為準。

| 介面 | 它回答的問題 |
|---|---|
| Batch script 骨架 | 「一個正確的 `#SBATCH` header 長什麼樣？」 |
| 資源請求 | 「`--mem` / `--cpus-per-task` / `--gres` / `--time` 實際上強制了什麼？」 |
| 串接與等待 | 「怎麼在 A 之後跑 B，而不用一直顧著 queue？」 |
| 隔離章節 | 「如果隔壁的 job 出包，我會不會被拖下水？」 |
| `references/gpu-isolation.md` | 「怎麼限制 GPU VRAM —— shard vs MPS vs MIG？」 |

## 這個 skill 真正圍繞的問題

**一個亂搞的 job 會不會只有它自己掛？** CPU 與 RAM 的答案是會：在
`task/cgroup` 下，job 被釘在自己的 core 上、被 `--mem` 硬性上限卡住，超過就
觸發 kernel OOM killer，**而且只在那個 job 自己的 cgroup 內**。鄰居不受影響。

但 GPU 記憶體不一樣 —— **配到一張 GPU 並不會限制它的記憶體**，而且各種選項在
「是否真的築起圍籬」這件事上差很多：

| 方法 | VRAM 隔離 | 只有它自己掛？ |
|---|---|---|
| `--gres=gpu:N`（整張卡） | 不適用（獨佔） | — |
| `--gres=shard:N` | **沒有** —— 只是記帳 | ❌ 可能把整張卡 OOM 掉 |
| `--gres=mps:N`（純的） | 沒有 | ❌ |
| `--gres=mps:N` + `CUDA_MPS_PINNED_DEVICE_MEM_LIMIT` | 有強制上限 | ✅ |
| **MIG**（`--gres=gpu:1g.5gb:1`） | **硬體切片** | ✅ 最強 |

**共用一張 GPU 不等於隔離一張 GPU。** Slurm 官方文件自己就寫 sharding
「does not fence the processes」—— 所以一個 batch size 設錯的 job 會把整張卡
連同鄰居一起帶走。`references/gpu-isolation.md` 有 `slurm.conf` / `gres.conf`
的設定片段、MPS 記憶體上限所需的 TaskProlog 接法，以及 MIG 的前提條件。

## 串接與等待

之所以補上，是因為這個 skill 原本對「怎麼在 A 之後跑 B」**完全沒有答案** ——
只有一次性的 `squeue` / `sacct` 檢視。

```bash
JID=$(sbatch --parsable phase_a.sbatch); JID=${JID%%;*}   # 剝掉 ";cluster"
sbatch --dependency=afterok:"$JID" \
       --kill-on-invalid-dep=yes \
       --mail-type=INVALID_DEPEND,END,FAIL \
       phase_b.sbatch
```

| Dependency | 在 parent…時觸發 |
|---|---|
| `afterok:<id>` | 成功（exit 0） |
| `afternotok:<id>` | 失敗 —— 用來掛告警 / 清理 |
| `afterany:<id>` | 結束，成敗皆可（**這是預設值**） |
| `after:<id>[+min]` | 開始執行 |
| `aftercorr:<id>` | array 的第 N 個任務接 parent array 的第 N 個 |
| `singleton` | 同名同使用者的前一個 job 結束 |

`,` 表示**全部**都要滿足；`?` 表示**任一**滿足即可。

若要用 block 而非串接：`sbatch --wait` ——
*"Do not exit until the submitted job terminates"*，並帶回 job 的 exit code。

至於 agent 端的問題 —— ***我**該怎麼等？* —— 這個 skill 交棒給
[`long-running-jobs`](long-running-jobs.zh-TW.md)，那裡把 scheduler 串接、
單次 blocking 背景等待、過濾後的事件串流、定時回檢排出了優先序。

## 代價最高的四個 gotcha

- **`afterany` 是預設的 dependency type。** 光寫 `-d 12345` 會讓 child 在
  parent 結束後就跑 —— **包含 parent 崩潰的情況**。永遠把 `afterok:` 寫出來。
- **Parent 失敗會讓 child 永遠卡在 `PENDING`。** Slurm 預設是
  *"the job stays pending with reason DependencyNeverSatisfied"*，看起來跟
  「在等資源」一模一樣；而且
  *"the dependent job will never be run, even if the preceding job is requeued"*。
  請加上 `--kill-on-invalid-dep=yes`。這個坑有自己的
  [pitfall 頁面](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/slurm-dependent-job-pends-forever-after-failed-parent.md)。
- **`--parsable` 印的是 `jobid;cluster`**，在有設定 cluster 名稱時並不是純
  job id。用 `${JID%%;*}` 剝掉 —— 否則 dependency 字串是壞的，**而且** `;`
  還會把你的 shell 指令截斷。
- **`sbatch --wait` 把所有 signal 死法都壓成 exit 1。** OOM 被殺、`TIMEOUT`、
  `scancel`、單純的 `exit 1` 全部分不出來。請讀
  `sacct -j <id> --format=State,ExitCode` —— `OUT_OF_MEMORY` / `TIMEOUT` /
  `NODE_FAIL` 這些狀態才告訴你「重跑有沒有機會成功」。

此外：`--mem` 是 cgroup 硬性上限而非建議值；`sacct` 需要設定 `slurmdbd`
（否則退回 `scontrol show job`，只有即時資料）；站點的 `Prolog`/`Epilog` 失敗
會讓 node 進入 drain；在 consumable resources 下 `srun --oversubscribe` 會被忽略。

## 什麼時候會觸發

- 寫或修 `sbatch` script、`srun` 指令列。
- 挑資源請求（CPU、記憶體、GPU、時間、partition）。
- 讀 job / queue / node 狀態（`squeue`、`sacct`、`sinfo`、`scontrol`）。
- 串接 job，或追問「為什麼相依的 job 一直沒開始」。
- 推理 cgroup 與「什麼能真的圍住 GPU VRAM」。

## 什麼時候不該用

- 操作某個專案專屬 cluster 的既有慣例 → 用那個 repo 的 skill。
- 從零設計 cluster provisioning / `slurm.conf` → 那是管理員的工作。
- 「*agent* 該怎麼等這個 job？」→ [`long-running-jobs`](long-running-jobs.zh-TW.md)。

## 結構

```
skills/local/slurm-hpc/
├── SKILL.md                        # 骨架、資源、串接、隔離、gotchas
└── references/
    └── gpu-isolation.md            # shard vs mps vs MIG、設定片段、強制細節
```
