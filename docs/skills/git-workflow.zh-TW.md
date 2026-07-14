# git-workflow

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：快轉合併
    (fast-forward merge)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `rebase`、`worktree`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

一套有主張、隨規模調整 (scale-aware) 的 git 工作流，從個人週末專案到多人、
多月的大專案都保持一致——讓 commit message、branch 命名、合併策略、release
tag 不再每個專案各自為政。Commit 一律用**英文**並遵循 Conventional Commits，
即使 prompt 是其他語言。

| Surface | 回答的問題 |
|---|---|
| `references/project-tiers.md` | 「該直接 commit 到 `main`、開 `dev` branch、還是走 PR？」 |
| `references/conventional-commits.md` | 「Commit message 到底要寫什麼？」 |
| `references/worktrees-parallel-agents.md` | 「怎麼平行跑多個 agent 又不互相衝突？」 |
| `references/versioning-and-releases.md` | 「什麼時候、怎麼打版本 tag？」 |
| `references/branch-hygiene.md` | 「哪些 local branch 做完了、哪些還在開發？」 |
| `scripts/branch-status.sh` | 同上，但以資料形式——分類每個 local branch。 |
| `scripts/check-commit-msg.sh` | 「這則 commit message 合法嗎？」 |
| `references/lazygit-cheatsheet.md` | 「這個操作在 lazygit 怎麼做？」（學習輔助） |

想了解這些預設背後的**原因**（概念而非 skill 機制），讀搭配的科普說明：
[Git workflow best practices](../reference/git-workflow.md)。

## 何時觸發

- 「Commit this」/「幫我 commit」/「整理一下 git」/「寫個 commit message」。
- 「該開 branch 還是直接 commit 到 main？」/「要開 PR 嗎？」
- 「幫平行 agent 設定 worktree」/「把我的 `.env` 帶進 worktree」。
- 「怎麼打 tag / 發 release？」/「bump 版本」。
- 「我的 local branch 一團亂——哪些做完了？」/「清理 branch」。
- 開新 repo，想要一套一致的 commit/branch/release 慣例給自己與 agent 用。

## 三個 tier（層級）

把繁瑣度 (ceremony) 對應到真實的協作需求；只有在訊號 (signal) 出現時才升級。

| Tier | 形狀 | 分支 | 整合 |
|---|---|---|---|
| **1 — 個人 / 早期** | 單一 `main` | commit 到 `main`；短命 local branch 可選 | `pull --rebase`、`merge --ff-only` |
| **2 — prod/dev 分流** | `main` = 已發布、`dev` = 整合 | feature branch 由 `dev` 切出 | 合併回 `dev`；release 時 ff `dev`→`main` |
| **3 — 多人 / 長大的 vibe-coding** | `main` 隨時可部署 | 短命 `feat/…` → PR | PR review/CI → squash-merge |

個人 vibe-coding 專案也可以直接跳到 Tier 3：即使只有一個人，PR 就是「ship
一個 feature」的分界，也是 CI 跑的地方。

## 預設一覽

- **Commit**：`type(scope): subject`——祈使句 (imperative)、小寫開頭、標題
  ≤72 字元、英文。`feat!`/`BREAKING CHANGE:` 觸發 major bump。
- **歷史**：線性——`pull.rebase=true`、`merge.ff=only`；嘈雜的 vibe-coding PR
  用 squash-merge，整理過的用 rebase-merge。
- **Branch**：人工意圖用 `feat/ fix/ chore/ docs/ refactor/ exp/`，agent/vibe
  工作用 `agent/…`，Claude worktree 用 `worktree-*`。
- **Worktree**：`claude --worktree <name>`；用 `.worktreeinclude`（只限被
  gitignore 的檔）把 `.env` 帶進去；把 `.claude/worktrees/` 加進 gitignore。
- **Release**：SemVer、annotated 且 `v` 前綴的 tag；若整個專案是 Python
  package，讓 git tag 驅動版本 (setuptools-scm / hatch-vcs)。
- **Forge CLI**：`gh` (GitHub) / `glab` (GitLab) 在終端機操作 PR——建議使用，
  但絕不硬性依賴。

## 結構

```
skills/local/git-workflow/
├── SKILL.md
├── scripts/
│   ├── branch-status.sh        # 分類 branch：active/merged/gone/stale
│   └── check-commit-msg.sh     # 驗證 Conventional Commits 標題
├── references/
│   ├── project-tiers.md        # main vs dev vs PR + GitHub Flow
│   ├── conventional-commits.md # commit message 規範精簡版
│   ├── worktrees-parallel-agents.md
│   ├── versioning-and-releases.md
│   ├── branch-hygiene.md
│   └── lazygit-cheatsheet.md   # 學習輔助
└── assets/
    ├── commit-template.txt      # git config commit.template
    └── worktreeinclude.template # .worktreeinclude 範例
```

## 與 secret 衛生 (hygiene) 的關係

這個 skill 把所有 secret 掃描與 agent transcript 處理都**交給**
[`agent-history-hygiene`](agent-history-hygiene.md)。在 commit/merge 時它呼叫
那個 skill 的 `scan-staged.sh`（exit `0` 乾淨 / `10` 已遮蔽 / `20` 有洩漏），
並指向其 rotate-first 的補救 runbook，而不自行重造。專案若不把 agent
transcript check in，就在 squash-merge 前移除；若有 check in，就用那個 skill
去 stage。

## Gotchas（陷阱）

- `merge.ff only` 會刻意拒絕分歧 (diverged) 的 pull——用 `git pull --rebase`
  解決。
- 被 squash-merge 的 branch 永遠不會出現在 `git branch --merged`；它會以
  upstream `gone` 呈現。`branch-status.sh` 會正確分類（確認沒有未推送
  (unpushed) 的工作後用 `-D` 刪）。
- `.worktreeinclude` 裡放已追蹤 (tracked) 的檔沒有作用——它只複製被 gitignore
  的比對項；已 commit 的 `.vscode/settings.json` 本來就在 worktree 裡。
- 英文 commit 規則在中文 prompt 下依然成立——翻譯意圖，不要把 prompt 語言
  照抄進歷史。

## 另見

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/git-workflow)
- [Git workflow best practices](../reference/git-workflow.md)——概念科普
  (Conventional Commits、SemVer、GitHub Flow、worktree)。
- [`agent-history-hygiene`](agent-history-hygiene.md)——這個 skill 在
  commit/merge 時交手的 secret + transcript 衛生。
