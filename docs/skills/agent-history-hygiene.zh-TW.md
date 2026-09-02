# agent-history-hygiene

!!! note "術語規則（zh-TW 頁面）"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文。
    程式碼、API 名、CLI flag、套件名與檔名一律不翻譯。

把 coding agent 的對話 transcript 與 plan 檔，跟它們產生的功能 diff 放進
**同一個 commit**，且不讓 `.env` 內容或 API key 進入 Git 歷史。

| 介面 (Surface) | 它回答的問題 |
|---|---|
| `run-specstory-session.sh` | 「怎麼替 recorder 建立可證明的 session 結束邊界？」 |
| `queue-agent-commit.sh` | 「live agent 怎麼要求稍後 commit，卻不碰仍在寫入的 transcript？」 |
| `finalize-agent-commit.sh` | 「writer 結束後，怎麼 sanitize、加 attribution 並 commit 那份精確 request？」 |
| `find-session.sh` | 「**我**目前 session 的 transcript / plan 是哪一個？」 |
| `stage-agent-artifacts.sh` | 「prepared commit 應包含哪些精確的 agent 檔？」 |
| `agent-commit-metadata.sh` | 「該帶哪些 harness/model 與 artifact trailers？」 |
| `bootstrap-project.sh` | 「怎麼安裝 validation-only artifact hooks 與 secret scanners？」 |
| `scan-staged.sh` | 「準備 commit 的內容裡有沒有洩漏的 secret？」 |
| `probe-specstory-redaction.py` | 「SpecStory 自己已經 redact 了什麼，不必重做？」 |
| `references/remediation.md` | 「已經 push 了 secret —— 現在怎麼辦？」 |

這個 skill 防止四種常見失敗：

1. Agent 把 `.specstory/history/*.md` 與 plan 看成 generated artifact，因而
   **默默漏掉**它們。
2. Transcript 捕捉到 credential，接著送進 Git 歷史。
3. Pre-commit 或 formatter 在 SpecStory 仍寫檔時改寫 transcript，之後又把
   較舊的 bytes restore 或 checkout 回去，蓋掉較新的歷史。
4. Commit 失敗後，尚未證明第一次是否成功，就從 LazyGit 或 CLI 再 commit
   一次。

## 生命週期不變量 (Lifecycle invariant)

Live transcript 不是一般 source file。安全邊界如下：

1. **Record：**在目標 worktree 啟動一個 foreground SpecStory/Claude
   session。Session 運行時只 stage 預定的 feature snapshot。
2. **Queue：**agent 寫入不具副作用的 request，精確記錄 session、rendered
   transcript、可選 plan、staged tree 與 base commit message。Queue 動作永遠
   不讀、不 stage、不 sanitize、也不 commit live transcript。
3. **Exit：**request 接受後，agent 不再做 repository 或 index 操作，並立即
   離開。Signal 或非零 child exit 只保留 request，不授予 finalization 權限。
4. **Synchronize：**只有 child 正常結束後，outer runner 才 render 精確
   session 並證明 sync 完成。
5. **Finalize：**由 parent 授權的 finalizer 重新驗證 worktree、branch、HEAD、
   staged tree、selectors、沒有 writer，以及沒有進行中的 Git operation。接著
   atomic stage 並 sanitize 精確 artifacts、從 prepared index 產生 provenance、
   驗證 message，最後只呼叫一次一般 commit。
6. **Continue：**只有 finalizer 證明狀態為 `committed` 或
   `already_committed` 後，才能開始 rebase、pull、switch、移除 worktree，或
   manual handoff。

這樣能維持 feature 與 transcript 同 commit 的語意，又不必要求 hook 在檔案
最不穩定的生命週期點改寫它們。

## 結構

```text
skills/local/agent-history-hygiene/
├── SKILL.md
├── scripts/
│   ├── run-specstory-session.sh              # foreground lifecycle owner
│   ├── queue-agent-commit.sh                 # inert exact commit request
│   ├── finalize-agent-commit.sh              # quiescent one-shot finalizer
│   ├── find-session.sh                       # exact session discovery
│   ├── stage-agent-artifacts.sh              # atomic exact artifact preparation
│   ├── agent-commit-metadata.sh              # staged provenance trailers
│   ├── bootstrap-project.sh                  # validation/scanner bootstrap
│   ├── probe-specstory-redaction.py          # native coverage measurement
│   └── scan-staged.sh                        # staged gitleaks wrapper
├── references/
│   ├── transcript-session-discovery.md
│   ├── pre-commit-redaction-stack.md
│   ├── specstory-native-redaction.md
│   └── remediation.md
└── assets/
    ├── artifact-dirs.txt
    ├── pre-commit-config.yaml.template
    ├── gitleaks.toml.template
    └── redact_secrets.py                     # finalizer-only mutator
```

## 預設工作流程：session 結束後 finalization

從目標 worktree 啟動 session。Parent authorization 可允許正常結束後自動呼叫
一次 finalizer；沒有授權時，runner 仍會完成精確的 post-exit sync，並保留
request 供明確的 recovery 使用。

```bash
# Parent shell：foreground recorder 與 lifecycle owner。
bash skills/local/agent-history-hygiene/scripts/run-specstory-session.sh \
  --allow-commit claude
```

在該 agent session 內：

1. Stage 本次 commit 應包含的 feature paths。
2. 取得 canonical session UUID 與精確 rendered transcript path；指定精確的
   plan，或明確聲明沒有 plan。
3. 把 base subject/body 寫入 message file；不要自行加入由 lifecycle 管理的
   provenance trailers。
4. 用 `queue-agent-commit.sh` 與上述精確 selectors/message 排入 commit
   request。
5. 回報 `finalization queued`，並立即退出。不要再執行 `git add`、
   `git commit`、rebase，或任何會寫 repository 的 diagnostic。

完整 selector 與 recovery flags 請看各 command 的 `--help`。公開 contract 的
重點是生命週期邊界，不是背下每個低階選項。

Finalizer 會驗證 staged feature tree 仍與 queued tree 相同。遇到 stale
HEAD/ref/index state、active transcript writer、不相關的 commit-message draft，
或進行中的 merge、cherry-pick、revert、bisect、rebase、sequencer、index lock，
都會拒絕。單獨殘留的 `REBASE_HEAD` 不能證明 rebase 仍 active；
`rebase-merge`、`rebase-apply` 與 `sequencer` 才是 active state。

### Commit 必須先於 rebase

先完成並證明 feature-plus-history commit，**之後**才能 rebase。一般 commit
的 hook 與 rebase/Git 本身都可能執行 checkout/restore，所以只要 recorder
仍可能 append tracked transcript，兩者都不安全。順序固定為：

```text
stage feature → queue → exit recorder → exact sync → finalize and prove commit
→ rebase/pull/merge if needed → push or retire
```

不要 rebase 尚未 finalization 的 staged change，也不要因為一般 commit 只
snapshot 一次 index，就以為它能在 live writer 下安全執行。會改檔的
pre-commit hook 仍可能把舊 working-tree bytes restore 到 live write 上。

### LazyGit 與 CLI draft 不授予 retry 權限

準備好精確 tree 與完整 message 後，finalizer 會先為 LazyGit 與 Git CLI 的
message location 寫入一致的 private drafts，再自行嘗試一次一般 commit。它
不會覆寫不相關或已被使用者編輯的 draft，也不會做 partial handoff。

這些 drafts 提供可見性與 recovery context，**不是**第二條 commit path 的
授權。依 bounded finalizer status 行動：

- `committed` / `already_committed`：已證明精確 parent、tree 與 lifecycle
  trailer；可以進行後續 Git operation。
- `commit_failed` 且精確 prepared snapshot 保留：先修 hook 或 dependency，
  再用新的 explicit authorization 呼叫 finalizer。不要在 LazyGit 按 Commit，
  也不要另跑 `git commit`。
- 結果不確定、snapshot 已改變，或 `commit_recovery_required`：只能核對 HEAD
  與 private journal。除非先證明前一次結果，否則不得透過 LazyGit、raw Git
  或 finalizer retry。
- `rotation_required`：先在 provider 端 rotate credential，再走明確確認過的
  recovery；prepared recovery 不會重新 stage。

## Validation-only hooks 與 mutator 範圍

`bootstrap-project.sh` 安裝釘選的 validation-only agent-artifact check、
gitleaks，以及標準 repository hygiene。Artifact check 與 scanners 可以檢查
staged snapshot，但不得改寫 index 或 working tree。Redaction 由 transcript
writer 已停止後的 post-session finalizer 負責。

所有 generic mutator——formatter、linter autofix、codemod、
`end-of-file-fixer`、`trailing-whitespace`——都必須排除每個 archival 與
skill-install root：

```text
.agents  .claude  .codex  .cursor  .opencode  .specify  .specstory
```

上述 roots 仍保留 detection coverage。即使已排除 `.agents`，也要另外排除
`.claude`，因為 `.claude/skills/<name>` 可能 symlink 到同一個 installed tree。
除了 recorder 自身，唯一獲准把 sanitized transcript bytes materialize 回去的
component 是 finalizer，而且只能在 lifecycle quiescence 後執行。

可選的 `prepare-commit-msg` integration 同樣是 validation-only。它會以 commit
實際使用的 index（包含一般 Git mode 建立的 temporary index）檢查明確 session
identity，但不 stage 或 repair 檔案。只要 `core.hooksPath` 有設定——即使是空值、
relative 或 external path——bootstrap 都拒絕自動安裝；請刻意整合到已設定的
hook directory。

## 精確 discovery 與 staging

`find-session.sh` 預設採精確模式。它驗證 SpecStory prologue、canonical
lowercase UUID、direct non-symlink transcript path、strict Claude JSONL 與
canonical worktree root。同一 UUID 可能 render 成多個 alias，因此 ambiguity
必須用明確 transcript path 解決；`--newest` 只是 compatibility escape hatch。

`stage-agent-artifacts.sh` 在同 commit workflow 中要求 non-artifact feature
diff。Preparation 在真正的 worktree index lock 下使用 alternate index，只有
全部成功才 atomic publish；validation mode 完全不修改 index。Finalizer 使用
exact selector path；branch-wide broad staging 只是 compatibility mode，不是
lifecycle 預設。

## SpecStory 2.10 的 checkout scope

Rendered output 與 Claude raw-session discovery 都依 **checkout path，而不是
branch** 分隔。同一 checkout 切換 branch 仍共用 artifact pool；不同 worktree
才有獨立的 `.specstory/history/` root 與 Claude project slug。

採用 **先建 worktree，再啟動 recorder/session** 的順序，每個 change stream
只跑一組 SpecStory wrapper 與 Claude session。`EnterWorktree` 不會重新綁定
既有 watcher；請停止它，再從目標 worktree 啟動 foreground runner。

## SpecStory 原生 redaction（v2.4.0+）

SpecStory 預設在寫檔時透過 Betterleaks redact，涵蓋 local Markdown 與 cloud
sync。Repository layer 仍不可少，因為實測 coverage 並不完整，尤其漏掉散文
中的 custom key 與 webhook shapes。

| 由誰攔下 | 組數（於 2.9.0 實測） | 例子 |
|---|---:|---|
| SpecStory | 36 / 54 | 主要 provider keys、PEM blocks、`.env` dumps |
| 只有 repository layer | 15 / 54 | 散文中的 Cursor、Tailscale、webhook 與 custom-key shapes |
| 都沒攔到 | 3 / 54 | access-key ID 與一個 bot-token 散文案例 |

兩層都使用 `[REDACTED:<rule-id>]`，gitleaks 也 allowlist 該 sentinel。Finalizer
不會改動 SpecStory 已 sanitize 的 bytes，也不會把 transcript、diff、scanner
或 credential 內容印到 bounded public output。

## 洩漏後的紀律 (Post-leak discipline)

任一層發現真正的 credential 時：

1. **先在 provider 端 rotate。** 這是唯一會撤銷 credential 的動作。
2. 評估它只被 staged、只在 local commit、已 push 到 feature branch，或已到
   shared branch。
3. 只有 rotate-first runbook 判定適合時才 scrub 歷史。永遠不要對 shared
   branch 使用 plain force-push。

任何 history rewrite 前先讀 `references/remediation.md`。

## Gotchas

- 絕對不要整體 ignore `.specstory/` 或 `.specstory/history/`；只精確排除
  machine-local identity 與 generated statistics。
- Normal child exit 加上 exact completed sync 才是 lifecycle proof；拿到 request
  file 不等於擁有 commit authority。
- Live writer 會阻擋 artifact staging 與 commit preparation。不要用一般 commit
  或 pre-commit mutator 繞過 guard。
- Branch name 不限制 SpecStory discovery；checkout path 才會。
- Claude/Cursor native attribution 可以疊加。Portable minimum 是 final staged
  `AI-Assisted-By` 加 transcript/plan block；message attribution 不是
  cryptographic signing。
- 散文中單純討論 private key 並不是 key material。出貨的 fixture 會在 runtime
  組合 scanner-sensitive header，而不是放寬 scanner coverage。
- `pre-commit install` 是 per clone；global `core.hooksPath` 也只會保護確實帶有
  預期設定的 repository。

## 另見

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/agent-history-hygiene)
- [Formatter 改寫已 commit 的 agent transcripts](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/formatter-rewrites-committed-agent-transcripts.md)
- [Pre-commit restore 蓋過 live SpecStory writes](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/pre-commit-restores-over-live-specstory-writes.md)
- [Live transcript 使 rebase continue 在 clean index 上失敗](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/rebase-continue-refuses-on-clean-index-live-transcript.md)
- [`project-knowledge-harness`](project-knowledge-harness.md) —— 互補的 durable
  project memory；本 skill 提供 agent review artifacts 所需的 Git lifecycle。
