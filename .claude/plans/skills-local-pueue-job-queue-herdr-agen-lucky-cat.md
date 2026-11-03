# Pueue → Herdr／Herdr Core：完成通知與 agent 續跑研究

## Context

使用者希望 a/b/c jobs 結束後，由 d 喚回原 agent 繼續工作，或帶著預設 prompt 與結果啟動乾淨的新 conversation；尤其適用於沒有 harness-native 喚醒機制的環境。這次先做可重現的小型實驗，再評估收錄到 `pueue-job-queue`，不直接建造完整 agent 編排框架。

**目前只有唯讀研究，尚未跑 jobs、傳送 prompts、安裝 Core 或修改 skill。**

## 初步研究結論

**建議採用「Pueue 管 jobs + 持久結果檔 + 可選續跑入口」；目前的 Herdr pane 用 Herdr，Core 另作獨立實驗。**

| 問題 | 已確認的行為與影響 |
|---|---|
| d after a/b/c | `--after` 是 all-success；任一上游失敗，d 變成 `DependencyFailed`，通知程式不會執行。 |
| 不論成功失敗都回報 | 複用 `wait.py --ids ...`，不加 `--fail-fast`；獨立 control group 等待，不占 worker group 的 slot。 |
| 回到原 Herdr agent | `herdr agent prompt` 可提交下一輪輸入；`notification show` 只是給人的 toast，不能代替 agent prompt。 |
| 乾淨的新 context | 新 pane + 正常啟動新 agent，再傳入 handoff prompt；不用 resume/fork。新 conversation 仍會載入一般 system/project instructions。 |
| 新 Core | `hc send` 是 PTY paste + Enter，不是 durable inbox；Core 使用 OSC 7501 狀態，不辨識 agent 品牌或畫面。 |
| Core 是否能直接控制現在的 pane | 未找到舊 Herdr pane registry 的 bridge；Core 有自己的 `HC_SESSION`／`HC_SOCKET`／terminal IDs，不能直接互換。 |
| Core parent/child 通知 | 自動 notes 涵蓋 blocked/error/exit，不是每個 done turn；外部 worker 可透過 `hc run --parent <hc-address>` 明確建立關係，但不因此繼承 parent caller context。 |
| 不經 Herdr 的對照 | 本機 Codex 已有 `queue --thread ... --message ... [--resume]`。它不等於 Monitor；queue 成功也不保證 resume 成功。列為版本限定的替代入口，不擴充本次範圍。 |

版本證據：本機 Herdr client/server **0.9.5 / protocol 22**、Pueue **4.0.2**、Codex **0.166.0**；`HERDR_ENV=1`，`hc` 不在 PATH。Core 原始碼研究以 **b63ecbd1** 為基準，實測時記錄完整 commit／binary version。

## 執行計畫

### 1. 保存研究與建立隔離實驗

- 依專案流程追蹤評估／實作，使用 td 記錄測試與 handoff；評估對應 Discussion，確定收錄的修改對應 Issue/worktree。不 commit、push 或 merge。
- 新增 `backlog/pueue-herdr-continuation.md`，記錄版本、來源、指令、證據、限制與採納判斷；區分 **runtime-verified / source-verified / skipped**。
- 複用 `tests/conftest.py:59-151` 的 `pueue_env`：獨立 `PUEUE_CONFIG_PATH`、socket、state、teardown。不觸碰使用者真實 queue 或 daemon callback。
- Herdr 僅建立專用、`--no-focus` 的 sibling 測試 pane，保留 cwd，不向目前這段對話或其他現有 agent 發送測試訊息。關閉時只清理自己建立的資源。
- Core 使用官方可核驗、固定版本的暫存 prebuilt binary，不跑全域 installer；獨立下載目錄與 script 目錄，設定唯一 `HC_SESSION` 及獨立 `XDG_STATE_HOME`／`XDG_CONFIG_HOME`／`XDG_RUNTIME_DIR`／`HC_SOCKET`。只改 socket 不會隔離 state，只改 session 不會隔離 templates。清除繼承的 hc caller identity，且任何可能自動啟 daemon 的 hc 指令都先套用隔離設定。若完整隔離或來源驗證不可行，跳過 Core runtime 測試，不升級／重啟現有 Herdr。

### 2. 驗證 a/b/c → 完成結果

使用只輸出短文字／寫暫存 artifact 的三個 jobs：

1. **all-success**：d 使用真正 `--after`；以時間戳證明 d 不早於所有上游結束。
2. **all-settled**：獨立 control group 的 d 不帶 success dependency；用 `wait.py` 等明確 IDs，確認一個 job 失敗時仍等較慢的其他 jobs 結束，再產生回報。
3. **負面情境**：失敗後 pause、有限 timeout、task 被移除、worker group parallelism=1。不自動 resume 使用者 queue，也不把不完整觀察說成全部完成。

**完成契約：** 不能只看 `wait.py` exit 0/5；exit 5 也可能是 task vanished。驗證 stdout JSON、完整預期 ID 集合、每個 `state == "Done"` 後，才原子寫入 `result.json`。timeout／missing 分別記為 incomplete／observation failure。

結果檔保留 `run_id`、task IDs、job outcomes、短摘要與 artifact paths；另存 delivery outcome。先持久化，再發通知，不能讓發送失敗遺失 job 結果。避免把完整環境變數或未篩選的大量 logs 塞入 prompt。

### 3. 驗證兩種續跑

**A. 原 Herdr conversation**

- 排程時固定 socket/session routing、pane ID、`terminal_id`、可取得的 `agent_session`、cwd 與 run ID；發送前重查，不依赖當下 focused pane。
- 僅對身份吻合的 idle/done agent 自動發送。working 暫緩，blocked/unknown、目標消失或替換則保留待處理結果，不注入按鍵、不繞過 approval。
- 使用 `agent prompt`，要求回覆唯一 `ACK:<run_id>` 與合成結果摘要，藉實際輸出確認新 turn，而非僅靠 command exit 或 `--wait`。
- Herdr prompt API 沒有 expected-session compare-and-send；身份預查仍有競態，不能宣稱嚴格防誤投／exactly-once。發送後 timeout/stall 記為 delivery unknown，不盲目重送。

**B. 全新 conversation**

- jobs 結束、結果檔穩定後才建立新 shell pane；解析建立回應的 ID，`agent start` 後傳 handoff。
- handoff 分成「預先授權的下一步」與「不可信 job 結果」；提供簡短摘要／檔案路徑，不把輸出中的指令當作新授權。
- 用新 session identity、非 resume/fork 的啟動參數與結果 ACK 驗證乾淨交接。這個模式不需要保留原 agent history，也不必保持原 pane 活著。

**模型成本界線：** 先以本地 receiver／stub 驗證大部分控制流程；Herdr 最多 3 個極短 Codex turns（初始、續跑、新 session），Core 通過隔離檢查後最多再 2 個。只處理合成資料、不要求改專案或執行工具；不加 permission-bypass，不自動接受 trust/approval。

### 4. Core 的對照測試

- 只操作本次 `hc` 建立並回傳的 terminal addresses；不將既有 `HERDR_PANE_ID` 當 hc target。
- 分別觀察 PTY 收到文字與真實 agent 是否開始處理；沒有 OSC status 不得推斷為 idle/done。模板預設等待 OSC readiness；檢查 `first_message.sent`／`started`，不能把 `--bg` 返回當成首訊息成功。`ready: quiet` 只表示輸出穩定，不作安全 readiness 的替代證據。
- 確認 `hc send` 的 working/blocked 行為；不使用 force。`--if idle` 有原子 status guard，但只匹配 idle、不含 done，也不是身份 guard。驗證外部 pueue worker 能明確指定 parent/target，而不是依賴 worker 恰好繼承正確環境。
- fresh follow-up 若要獨立於原 agent 存活，使用 `--no-parent`；若保留親子關係，明確評估 `--outlive-parent`，因為預設 child 會隨 parent 結束。`--parent` 不會自動注入正確的回覆地址，需要明寫 handoff instructions。
- 用小型 OSC-reporting receiver 測 parent 的 blocked/error/exit notes；分清「process exit」與「仍存活 agent 的 turn done」。不要把自動 notes 當成可靠 completion hook。
- 評估重點是 Core 是否適合作為新、headless 流程的入口；不做 Herdr→Core 遷移或跨 registry adapter。

### 5. 僅收錄通過實驗的最小 recipe

推薦收錄 **reference + 少量 gotchas**，不要先新增通用 dispatcher。

- `skills/local/pueue-job-queue/references/agent-continuation.md`：新增兩種完成條件、兩種交接流程、Herdr/Core 選擇規則、實測版本与復原方式。Core 未通過 runtime 驗證時，只記研究限制，不宣稱正式支援。
- `skills/local/pueue-job-queue/SKILL.md`：加入按需閱讀入口；補上 success-only 通知陷阱、完整完成驗證、送達不等於處理的 gotchas；順帶把既有 wait JSON 示例的 `status` 修正為實際 `state`。
- `skills/local/pueue-job-queue/tests/test_completion_handoff.py`（必要時擴充現有 `test_wait.py`）：保留可重現的 queue timing、all-settled、invalid/incomplete result、receiver ACK 與 no-blind-retry 測試，不依賴真實 Herdr/LLM 才能跑基本 suite。
- `skills/local/pueue-job-queue/tests/README.md`：說明自動測試和 opt-in live smoke 的界線。

**維持不變：** `submit-dag.py` schema、`wait.py` 的既有對外契約、全域 daemon 設定、vendored Herdr、marketplace、discovery symlinks。不新增常駐服務、重試資料庫、跨 runtime ID 映射。未通過的流程留在研究文件並說明 blocker。

## 複用點

- `scripts/submit-dag.py`：拓樸提交、`--isolated-group`、name→task ID mapping。
- `scripts/wait.py:182-280`：固定 ID 集合、有限 timeout、JSON summary；不要重新實作等待器或使用 union selectors 擴大集合。
- `tests/conftest.py` 的 `pueue_env` 與 `tests/test_dag.py` 時間戳斷言。
- `skills/local/long-running-jobs/references/completion-contracts.md` 的 durable artifact 原則，不建立新的 completion 框架。

## Verification / 驗收

```bash
uv run --extra dev pytest skills/local/pueue-job-queue/tests/ -q
bash skills/local/pueue-job-queue/tests/test_contracts.sh
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/pueue-job-queue
make validate
```

Live smoke 必須保存：版本、job 開始／結束時序、完成結果檔、目標 session identity、ACK／新 turn 證據及 cleanup 清單。明確列出 busy/blocked/replaced/missing、ambiguous delivery 哪些由 stub 驗證、哪些真實執行，不能混為 end-to-end 成功。

最終交付回答：**兩種場景是否可行、現有 Herdr 與 Core 分別適用哪裡、實際測過什麼、哪些 recipe 值得進 skill，以及仍不提供什麼保證。**

## 主要來源

- [Herdr Core 介紹](https://herdr.dev/core/)
- [Herdr Core 原始碼與 README](https://github.com/herdrdev/herdr-core)
- [Core command reference](https://github.com/herdrdev/herdr-core/blob/master/docs/commands.md)
- [Core templates](https://github.com/herdrdev/herdr-core/blob/master/docs/templates.md)
- [Core API](https://github.com/herdrdev/herdr-core/blob/master/schema/README.md)
- [Herdr 0.9.5 socket API](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/socket-api.mdx)
- 本機 `herdr --help`／`herdr api schema --json`、`pueue add --help`、`codex queue --help`。
