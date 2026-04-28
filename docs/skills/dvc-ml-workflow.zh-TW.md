# dvc-ml-workflow

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

DVC ([Data Version Control](https://dvc.org/doc)，upstream
[treeverse/dvc](https://github.com/treeverse/dvc)) 把 git repo 變成完整
的 ML 實驗室：資料與模型檔案做 out-of-band 版本化、pipeline 在
`dvc.yaml` 中宣告、experiment 以 **ephemeral git commit** 形式跑出來
並附帶 metric 跟 plot。沒有 tracking server、沒有獨立 database ——
所有東西都活在你既有的 git history 裡。

這個 skill 對 DVC 中關係到 production ML 工作的部分有特定意見：
pipeline、metrics 自動繫結到 commit 的 queued experiment、以及
remote storage。其他事情則交給官方文件
[dvc.org/doc](https://dvc.org/doc)，並 inline 連結。

> Iterative 在 2024 被 Treeverse 收購。`pip install dvc` 解析到
> [github.com/treeverse/dvc](https://github.com/treeverse/dvc) ——
> 從舊的 `iterative/dvc` redirect 過來。

## 出貨內容 (What ships)

- 完整 SKILL.md
  ([skills/local/dvc-ml-workflow/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/SKILL.md))
  含三模式心智模型 (`add` / pipeline / `exp run`)、決策工作流程、
  以及對應實際 production 失敗 calibrate 過的 gotcha 區段。
- 四份 reference —— 按需讀取，不預先載入 context：
    - [`pipelines-and-stages.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/pipelines-and-stages.md)
      —— `dvc.yaml` schema、`foreach` 矩陣 stage、`frozen`、
      `always_changed`。
    - [`experiments-and-queue.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/experiments-and-queue.md)
      —— `dvc exp run --queue`、`dvc queue start --jobs N`、
      ephemeral-commit 語義、`dvc exp apply` / `branch` / `gc`。
    - [`data-and-remotes.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/data-and-remotes.md)
      —— S3 / GCS / Azure / SSH / GDrive / MinIO setup、credential 處理。
    - [`plots-and-metrics.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/references/plots-and-metrics.md)
      —— `dvc metrics diff`、plot template、confusion matrix、
      VS Code extension。
- 三個 script：
    - [`init-dvc-project.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/scripts/init-dvc-project.sh)
      —— idempotent 的 `dvc init` + `.gitignore` + 可選的
      `dvc remote add` + 不存在時放置 template。
    - [`queue-helper.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/scripts/queue-helper.sh)
      —— 對 `dvc queue` 的 agent-friendly 包裝，含 `grid` subcommand
      做笛卡兒積 enqueue 一次完成。JSON stdout。
    - [`lint-dvcyaml.sh`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/scripts/lint-dvcyaml.sh)
      —— 只 parse 的 validator (`dvc dag --dot`)，schema error 時
      非零退出但不跑任何 stage。
- 三個 `assets/` template：
  [`dvc.yaml.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/assets/dvc.yaml.template)、
  [`params.yaml.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/assets/params.yaml.template)、
  [`.dvcignore.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/dvc-ml-workflow/assets/.dvcignore.template)。

## 為什麼選 DVC（一段話）

如果你已經在 git 上，要在不立 tracking server 的前提下取得可重現性，
DVC 很難被打敗。殺手級功能是 `dvc exp run --queue` +
`dvc queue start --jobs N` 平行跑參數掃，**每次完成的 run 都是
`refs/exps/` 中的真實 commit**，metric、param、output 一起綁好 ——
不需要獨立 database 對齊。用 `dvc exp apply` 把一個 promote 成 branch、
其餘用 `dvc exp gc` garbage-collect。`dvc.yaml` pipeline 格式還給你
變更偵測 (`dvc repro` 只重跑 dep 變了的 stage)，這是 `make` 對二進位
輸入做不到的。

## 快速開始

```bash
# 在現有 git repo 的目前目錄初始化：
bash skills/local/dvc-ml-workflow/scripts/init-dvc-project.sh \
  --remote s3://my-bucket/dvc-store

# 編輯 dvc.yaml + params.yaml template，然後：
dvc repro                                  # 跑一次 pipeline
dvc exp run -S model.lr=1e-3              # 試另一個 LR
dvc exp run --queue -S model.lr=5e-4      # queue 一個 sweep 條目
dvc queue start --jobs 4                  # 平行 worker
dvc exp show                              # 表格化比對
```

## Cross-references

- 官方文件：[dvc.org/doc](https://dvc.org/doc) —— 永遠連這個，不要
  從記憶 paraphrase；DVC 的 CLI 表面在 minor 版間會變。
- Upstream repo：[github.com/treeverse/dvc](https://github.com/treeverse/dvc)。
- VS Code extension：
  [marketplace.visualstudio.com/items?itemName=Iterative.dvc](https://marketplace.visualstudio.com/items?itemName=Iterative.dvc)
  —— 在編輯器內加上 live experiment 表格、含 parallel coordinates 的
  plot dashboard、以及 `dvc.yaml` schema 驗證。
