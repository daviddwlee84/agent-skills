# agent-history-hygiene

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

把 coding agent 的對話 transcript 與 plan 檔，跟它們產生的功能 diff 一起
commit，且不讓 `.env` 內容或 API key 漏到 git 歷史。

| 介面 (Surface) | 它回答的問題 |
|---|---|
| `find-session.sh` | 「**我**目前 session 的 transcript / plan 是哪一個？」 |
| `stage-agent-artifacts.sh` | 「下次 commit 應該包含哪些 agent 檔？」 |
| `agent-commit-metadata.sh` | 「這次 commit 該帶哪些 harness/model 與 artifact trailers？」 |
| `bootstrap-project.sh` | 「怎麼把 pre-commit + gitleaks + redactor 裝進新 repo？」 |
| `scan-staged.sh` | 「我準備 commit 的東西裡有沒有洩漏的 secret？」 |
| `probe-specstory-redaction.py` | 「SpecStory 自己已經 redact 了什麼，我們不用重做？」 |
| `references/remediation.md` | 「我已經 push 了 secret —— 現在怎麼辦？」 |

這個 skill 的存在是為了阻止三種常見失敗：

1. Agent 因為把 `.specstory/history/*.md` 跟 `.claude/plans/*.md` 看成
   生成 (generated) 產物，**默默地**從 commit 中漏掉它們。
2. 對話 transcript 中意外的 `.env` echo，被 commit 並 push 出去。
3. 洩漏後的 reflexive `git push --force` —— 它根本不會撤銷憑證
   (credential)，反而常常毀掉隊友的工作。

## skill 觸發時機

- 「Commit my chat」/「save the specstory session」/「stage the plan
  file」/「把 plan 跟 specstory 一起 commit 進去」。
- `git status` 中出現未追蹤的 `.specstory/history/*.md` 或
  `.claude/plans/*.md`。
- 「Scrub this transcript」/「redact my key」/「gitleaks flagged my
  chat history」。
- 「Set up pre-commit for this repo」/「bootstrap secret scanning」。
- 「I pushed a `.env`」/「a secret went to main」 —— skill 會把使用者
  導向 rotate-first runbook，而不是去做歷史改寫。

## 結構

```
skills/local/agent-history-hygiene/
├── SKILL.md                                  # agent-facing 工作流程與 invariants
├── scripts/
│   ├── find-session.sh                       # 定位目前 SpecStory + Claude session
│   ├── stage-agent-artifacts.sh              # git-add 對的 artifact
│   ├── agent-commit-metadata.sh               # 從 staged snapshot 產生 provenance trailers
│   ├── bootstrap-project.sh                  # 安裝 pre-commit + gitleaks，接上 redactor
│   ├── probe-specstory-redaction.py          # 量測 SpecStory 自身的 redaction 覆蓋率
│   └── scan-staged.sh                        # 帶 agent-friendly exit code 的 gitleaks 包裝
├── references/
│   ├── transcript-session-discovery.md       # SpecStory / Claude session 佈局
│   ├── pre-commit-redaction-stack.md         # 分層防禦設計
│   ├── specstory-native-redaction.md         # upstream 實測 redact 了什麼
│   └── remediation.md                        # rotate-first 洩漏處理流程
└── assets/
    ├── artifact-dirs.txt                     # 可設定的 agent artifact 目錄清單
    ├── pre-commit-config.yaml.template
    ├── gitleaks.toml.template
    └── redact_secrets.py                     # 直接在安裝好的 skill 原地執行
```

## 與 chezmoi 的整合

這個 skill 疊在使用者既有的 chezmoi 基礎設施之上（如有）：

- `~/.config/git/hooks/pre-commit`（全域 `core.hooksPath`）跑這個 skill
  在 repo 層級裝的 `.pre-commit-config.yaml`。
- `~/.local/share/chezmoi/scripts/redact_secrets.py` 原本是 upstream。
  現在 `assets/redact_secrets.py` 是 source of truth，並透過本 repo 根目錄的
  `.pre-commit-hooks.yaml` 以**釘選版本的 pre-commit hook** 形式送到下游 repo
  —— 沒有會走味的 vendored 副本。偏好 chezmoi 版本的 repo 仍可用
  `bootstrap-project.sh --from-chezmoi` symlink `.pre-commit-config.yaml` /
  `.gitleaks.toml`。
- `~/.local/share/chezmoi/.gitleaks.toml` 跟 skill 的
  `gitleaks.toml.template` 共用 rule ID，這樣 `.gitleaksignore` /
  allowlist 微調可在 repo 間 portable。

對沒有 chezmoi 的 repo，`bootstrap-project.sh` 產生自包含的 stack。
redactor **不會**被複製進 repo：產生的 `.pre-commit-config.yaml` 以 tag
引用該 hook，所以 `pre-commit autoupdate` 就能把修正送到每個 repo，
而且 script 路徑完全不依賴 `npx skills` 把 skill 裝在哪裡。

```yaml
- repo: https://github.com/daviddwlee84/agent-skills
  rev: ahh-v1.1.0
  hooks:
    - id: redact-agent-secrets
```

舊的 vendored `scripts/redact_secrets.py` 佈局可用
`bootstrap-project.sh --migrate` 轉換過來。

若 `core.hooksPath` 把 Git hook 導向 `.git/hooks/` 以外的位置，
`--install-hook` 會在寫入 bootstrap 檔案前拒絕執行，並提示把整合加入設定中的
hook directory，或只對該 repo 取消 override。Skill 不會自行修改 global hook。

## 預設工作流程：把功能跟對話一起 commit

```bash
# 1. 確保 agent 知道哪一個 session 是「我們的」。
bash skills/local/agent-history-hygiene/scripts/find-session.sh

# 2. Stage code，再自動 add agent artifact。
git add path/to/feature.ts
bash skills/local/agent-history-hygiene/scripts/stage-agent-artifacts.sh

# 3. 從 staged artifacts 產生 canonical final trailer block。
bash skills/local/agent-history-hygiene/scripts/agent-commit-metadata.sh

# 4. 掃描 secret，再驗證完整英文 commit message。
bash skills/local/agent-history-hygiene/scripts/scan-staged.sh
bash skills/local/git-workflow/scripts/check-commit-msg.sh \
  --agentic --staged --file /path/to/commit-message.txt

# 5. Commit。Pre-commit 會把 redact + gitleaks 當成 catch-all 再跑一次。
git commit -F /path/to/commit-message.txt
```

Metadata helper 讀 staged blob，而不是仍可能被背景程序修改的 working file。
它輸出去重後的 `AI-Assisted-By: Harness (model)`、`Agent-Transcript` 與有 plan
時的 `Agent-Plan`。只有 transcript 無法證明 identity 時，才同時傳入
`--harness` 與 `--model`。

## SpecStory 原生 redaction（v2.4.0+）

SpecStory 現在自己就會 redact secret，所以這個 skill 對
`.specstory/history/` 已經不是第一道防線了。

| 出處 | 內容 |
|---|---|
| [PR #235](https://github.com/specstoryai/getspecstory/pull/235) | `feat(redaction): automatically redact secrets from saved markdown history` —— 社群貢獻者 [@warnes](https://github.com/warnes) 提出，2026-07-20 merged |
| [PR #253](https://github.com/specstoryai/getspecstory/pull/253) | #235 的 `gofmt` CI 修正分支；最後 close 掉走 #235 |
| **v2.4.0**（2026-07-20） | 正式釋出，**預設開啟**，改用 [Betterleaks](https://github.com/betterleaks/betterleaks) ruleset，且涵蓋本地 markdown **與** cloud sync |
| [#274](https://github.com/specstoryai/getspecstory/issues/274)（open） | 相關的另一個洩漏面向 —— `specstory watch` 把 cloud auth token 放進 process command line |

實際 merge 的程式碼跟 PR 不同：維護者把 PR 裡 11 條 inline regex 換成
Betterleaks，而 PR 的 `extra_patterns`（自訂 regex）沒有在這次改寫中存活。
`.specstory/cli/config.toml` 的 `[redaction] enabled`（或 `--no-redact-secrets`）
是唯一的開關。

### 實測覆蓋率

`scripts/probe-specstory-redaction.py` 會合成一個 Claude Code session，
用 `specstory sync --print` 跑兩次（有 / 無 `--no-redact-secrets`），
再逐個 secret class 比對。對 specstory 2.9.0、共 54 組 class/context：

| 由誰攔下 | 組數 | 例子 |
|---|---:|---|
| SpecStory | 36 | Anthropic、OpenAI、GitHub PAT/OAuth/Actions、GitLab、Google、Groq、Slack、Stripe、Supabase、Linear、PEM block、`.env` dump |
| **只有我們** | 15 | Cursor、Tailscale、Discord/Zapier/Make webhook —— 以及 HuggingFace、Notion、WakaTime、OpenAI project key 出現在**散文**中時 |
| 都沒攔到 | 3 | `AKIA…` access key ID；散文中的 Telegram bot token |

結構性發現：Betterleaks 有好幾類只在 `KEY=value` 形式下、透過基於 entropy 的
`generic-api-key` rule 才攔得到。同一個 token 出現在句子裡 —— 而這正是工具
transcript 實際印出 token 的方式 —— 就會直接漏過去。我們以 prefix 錨定的
rule 不在乎前後語法。

### 兩層如何避免互相打架

兩邊都寫同一個 sentinel：`[REDACTED:<rule-id>]`（SpecStory 的 binary 帶有
格式字串 `[REDACTED:%s]`），而 `.gitleaks.toml` 把這個形狀加進 allowlist。
SpecStory 已經清理過的 transcript 會原封不動通過 hook —— 不會出現
「files were modified by this hook」，不用重新 `git add`，也不用再 commit 一次。

redactor 改寫成 `[REDACTED:<rule-id>]`，不再寫 `sk-abc...xyz` 截斷形式；
PEM block 則變成 `[REDACTED:private-key]` —— 正好就是 SpecStory 用的標籤。
截斷形式仍保留在 console 報告中，那裡的指紋有助於判斷該去 rotate 哪把 key。
`--legacy` 會改回 2.4.0 之前的 placeholder，它只改變寫入的位元組，
不影響偵測到什麼。

（另一條相關規則 —— 散文中單純提到 `PRIVATE KEY` 不算金鑰材料，
`detect-private-key` 找的是 `BEGIN … PRIVATE KEY` 標頭 —— 由 redactor
以標頭為範圍的比對獨立保證。）

## 洩漏後的紀律 (Post-leak discipline)

`scan-staged.sh` 的 exit code 依洩漏狀態分支 (0 clean、10 redacted、
20 leaks、30 沒裝 gitleaks)。當有洩漏溜過去：

1. **在供應商端輪換 (rotate)。** 這是唯一真正撤銷 credential 的動作。
   連結見 `references/remediation.md` §1。
2. **評估爆炸半徑 (blast radius)。** 本地未 push？feature branch？main？
3. **只在便宜時才清洗 (scrub)。** 未 push commit 用 amend 或
   `reset --soft`；feature branch 用 `git filter-repo` +
   force-with-lease；**永遠不要**改寫 `main`。

runbook 顯式禁止對共用 branch 做 `git push --force` —— 詳見
`references/remediation.md` §5。

## Gotchas

- 設定 `core.hooksPath` 後，`.git/hooks/prepare-commit-msg` 不會執行。
  `bootstrap-project.sh --install-hook` 現在會 exit 6，而不是安裝一個無效 hook。
- Claude/Cursor 原生 attribution 可以保留。可攜 minimum 是最後的
  `AI-Assisted-By` + transcript/plan block；不要虛構 AI email，也不要把 message
  attribution 說成 cryptographic signing。

- SpecStory ≥ 2.4.0 寫檔時就已經 redact —— 別讓 hook 再做一次，
  見上面的「SpecStory 原生 redaction」。
- 純文字提到 "PRIVATE KEY" 不算洩漏；`detect-private-key` 只比對
  `BEGIN … PRIVATE KEY` 標頭。改寫這種散文只會讓 transcript 白白 churn。
- 同一個 hook **不吃任何 allowlist** —— `<!-- gitleaks:allow -->` 不行，
  `.github/secret_scanning.yml` 也不行 —— 而 `npx skills add` 會把這個 skill
  的測試裝進你的掃描範圍內。因此本 skill 不再出貨任何字面的 key header
  （測試在 runtime 組出來，fixture 用 `__SYNTHETIC_PEM_*__` placeholder），
  由 `tests/test_shipped_file_hygiene.py` 把關。若舊版安裝擋住你的 commit
  （`Private key found: .agents/skills/agent-history-hygiene/tests/…`），
  請跑 `npx skills@latest update`，不要去放寬 `exclude:` ——
  [pitfall](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/detect-private-key-blocks-commits-in-downstream-repos.md)。
- Claude Code 的 project-level `plansDirectory` 有時會被忽略
  ([issue #19537](https://github.com/anthropics/claude-code/issues/19537))；
  把它設在 user-level (`~/.claude/settings.json`) 當預設。
- `gitleaks protect` 從 v8.19.0 起被棄用 —— 用 `gitleaks git --staged`。
  skill 中所有地方都用現代語法。
- `pre-commit install` 是 per-clone —— 每個隊友（跟 CI）都必須跑，
  hook 才會觸發。
- 全域 `core.hooksPath` 只在 repo 有 `.pre-commit-config.yaml` 時才執行；
  bootstrap 之前的裸 repo 是不受保護的。

## 另見

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/agent-history-hygiene)
- [`project-knowledge-harness`](project-knowledge-harness.md) ——
  互補的記憶 harness，把 `.claude/plans/` 視為 ephemeral 塗鴉本。
  這個 skill 補上閉環，確保那些塗鴉本實際上會落到 git 裡。
