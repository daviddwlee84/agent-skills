# colab-remote-runner

把 **Google Colab 當成用完即丟的遠端運算機器**跑批次 job，全程在 terminal 用官方
[Colab CLI](https://github.com/googlecolab/google-colab-cli)（`colab`）操作：
開 session、用 wheel 送程式碼、從 Google Drive 拉資料、在 GPU 或高 RAM 的 VM 上執行指令、
下載輸出、關掉 session。

從一個實際跑通的研究流程（量化模型訓練丟到 Colab T4 / high-RAM session）抽出來，並移除專案細節。

| 內容 | 回答的問題 |
|---|---|
| `SKILL.md` | 「預設流程是什麼？哪些坑會踩到？」 |
| [`scripts/colab_job.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/scripts/colab_job.py) | 「一鍵跑完」—— `exec` / `upload` / `run`、`--dry-run`、stdout 為 JSON |
| [`assets/remote_steps.py`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/assets/remote_steps.py) | VM 端的 `install` / `data` / `run` 步驟 |
| [`references/gotchas.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/gotchas.md) | 依錯誤訊息命名的坑（`400 Bad Request`、`mount failed`、`Timeout waiting for reply`、`RefreshError`） |
| [`references/drive-data.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/drive-data.md) | 資料放 Drive、sha256 manifest、Drive API 下載 |
| [`references/smoke-test.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/smoke-test.md) | 公開 Datasette 資料表 → 在 Colab 上跑 LightGBM（CPU）與 Keras（T4），附實測時間與花費 |
| [`references/adapting-to-a-project.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/colab-remote-runner/references/adapting-to-a-project.md) | 在專案裡包一層薄 wrapper 的做法 |

## 快速開始

```bash
uv tool install google-colab-cli
colab new -s work --gpu T4 --high-mem
colab auth -s work                     # 每個 session 互動式授權一次，才能用 Drive

colab_job.py --dry-run run -s work --wheel . --data-spec data.json \
    --cmd "my-train --out /content/job/out" --out runs/colab
colab_job.py run -s work --wheel . --data-spec data.json \
    --cmd "my-train --out /content/job/out" --out runs/colab

colab stop -s work                     # 閒置的 session 會持續計費
```

每次 `run` 都會在 stdout 印出一個 JSON，含**花費／時間區塊**：各階段的 `timing_s`
（session、upload、install、data、run、download、stop）、`cost`（`colab usage` 快照與
`units_estimated` = 費率 × 實際時間）、`vm`（Python、CPU、RAM、GPU）；同樣內容也寫進結果目錄的
`_colab_meta.json`，步驟失敗時也照樣回報。smoke test 端到端約 65 秒：CPU VM 約 0.001 compute units，
T4 約 0.02。

## 形塑這個 skill 的教訓

- **瓶頸是資料，不是 GPU。** 本機上傳到 VM 約 2 MB/s，單次請求有上限（約 60–94 MB）。
  5–6 GB 的資料讓一次 22 分鐘的 run 大半時間都在上傳。資料先放 Drive，VM 走 Google 內網下載。
- **`colab exec` 的結果不可盡信。** 遠端丟例外仍可能 exit 0；預設 30 秒「安靜」逾時會在
  安靜的步驟觸發。每個遠端步驟印出成功 marker，client 用長 timeout 並以 marker 為準。
- **`colab drivemount` 在無頭模式失敗。** 改用 `colab auth` + Drive API；但授權每個 session
  需要人工一次，所以一段工作期間沿用同一個 session。
- **CLI 0.8 把 token 移進 OS keyring。** 透過 SSH 時 keyring 常是鎖住的，每個指令會卡約 60 秒；
  用 `colab_job.py --no-keyring` 或 `colab --auth=adc` 避開。
- **結果在本機記錄。** 下載輸出目錄後，在本機用 tracker（例如 MLflow）記錄並打上
  `compute=colab` tag；VM 上不放任何 tracker 憑證。

## 不適用的情況

互動式 notebook 開發（用 Colab 網頁）、需要排隊／排程的多 job pipeline
（[`slurm-hpc`](slurm-hpc.md)、[`pueue-job-queue`](pueue-job-queue.md)），
或不允許存放在 Google Drive 的資料。
