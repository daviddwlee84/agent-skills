# Git workflow best practices — Git 工作流最佳實踐

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：快轉合併
    (fast-forward merge)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `rebase`、`squash`、`worktree`）。代碼、API 名、CLI flag、套件名、
    檔名一律不翻。

這是 [`git-workflow`](../skills/git-workflow.md) skill 所編碼慣例的概念層
說明。讀這篇是為了理解**原因**——它本身就能當入門讀物，不依賴 skill 的
scripts。全篇都偏好**乾淨、線性、可審閱 (reviewable) 的歷史**，以及能從個人
擴展到團隊的習慣。

## Commit message：Conventional Commits

Commit message 既是文件，也是給工具的 API。
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 慣例給
每則 commit 一個機器可讀的前綴：

```
<type>(<optional scope>): <subject>
```

常見 type：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、
`build`、`ci`、`chore`、`revert`。Subject 是簡短的**祈使句 (imperative)**
（「add retry」而非「added retry」）、小寫、無句點結尾，最好 ≤ 72 字元。`!`
（或 `BREAKING CHANGE:` footer）標示不相容 (incompatible) 的變更。

個人開發為什麼還要這麼做？因為 log 會變成可自動生成的 changelog、可計算的
版本 bump、以及幾個月後還能 `git log --grep 'feat'` 的歷史。即使你用其他
語言思考與下 prompt，commit 也一律**英文**——object graph 是給工具與未來的
協作者讀的。

## 語意化版本 (Semantic Versioning)

[SemVer](https://semver.org/) 用 `MAJOR.MINOR.PATCH` 標號 release：

- **MAJOR**——不相容 / 破壞性 (breaking) 變更。
- **MINOR**——新增且向後相容 (backward-compatible) 的功能。
- **PATCH**——向後相容的 bug 修復。

這乾淨對應到 Conventional Commits：`fix:` → PATCH、`feat:` → MINOR、任何
breaking → MAJOR。`1.0.0` 之前一切都可能改；`1.0.0` 是穩定公開介面的承諾。

## 依專案規模選工作流

最大的錯誤是把團隊的繁瑣度套到個人 repo（只有摩擦沒有好處），或把個人習慣
套到共享 repo（衝突、無法審閱的歷史）。把工作流對應到真實需求：

- **Tier 1 — 個人 / 早期。** 單一 `main`。直接 commit，用 `git pull --rebase`
  保持線性，偶爾用 `git merge --ff-only` 落地短命 branch。不開 PR。值得回頭
  的狀態就打 tag。
- **Tier 2 — prod/dev 分流。** `main` 是已發布 / 已部署的線；`dev` 是功能整合
  的地方。release 時把 `dev` → `main` 升級。當有東西（部署、隊友）依賴穩定線
  而你還在開發時採用。
- **Tier 3 — 團隊 / 長大的 vibe-coding。** `main` 隨時可部署；所有工作都在
  短命 branch 上、經 review 與 CI 後透過 **pull request** 合併。這就是
  [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)。
  即使個人專案也受益：PR 是「ship 一個 feature」的分界、CI 的觸發點、以及
  回滾 (revert) 點。

你可以跳級——重度 CI 的個人專案可以直接從 Tier 3 起步。

## Rebase、fast-forward 與 squash

三個操作形塑歷史：

- **`git pull --rebase`** 把你的 local commit 重播 (replay) 到抓下來的
  upstream *之上*，而非產生 merge commit，讓歷史保持線性。設為預設：
  `git config pull.rebase true`。
- **快轉合併 (fast-forward merge)**（`git merge --ff-only`）只把 branch 指標
  往前移、不產生 merge commit——只有在沒有東西需要調解 (reconcile) 時才可能。
  `git config merge.ff only` 讓 git *拒絕*會產生 merge commit 的合併，把分歧
  攤開而不是藏起來。
- **Squash merge** 把一個 branch 的所有 commit 壓成目標上的單一 commit。很適合
  充滿 work-in-progress 雜訊的 vibe-coding branch：主線只拿到一個乾淨的
  `feat: …` commit。代價是該 branch 的個別 commit 不會出現在 `main` 上——所以
  之後它會顯示為 `gone` 而非 `merged`（見 [Branch 命名](#branch)）。

原則：local 用 fast-forward 保持線性；嘈雜的 PR 用 squash；每個 commit 都有
意義的 PR 用 rebase-merge。

## Branch 命名

`<prefix>/<kebab-描述>` 慣例讓 branch 依意圖排序，也讓你能批次清理：

- 人工撰寫的工作用 `feat/…`、`fix/…`、`chore/…`、`docs/…`、`refactor/…`、
  `exp/…`（可帶 issue 編號：`feat/123-oauth`）。
- `agent/…` 作為 agent / vibe-coding branch 的獨立命名空間，讓機器生成的工作
  在視覺上分開、也可分開丟棄。
- `worktree-*` 是 Claude Code 為 worktree 自動建立的。

把這些命名空間分開，才能讓清理（`git branch --list 'agent/*'`）變得安全而非
提心吊膽。PR 合併後用 `git fetch --prune` 修剪；upstream 為 `gone` 的 branch
（`git branch -vv`）通常已完成——但刪除前先確認沒有未推送 (unpushed) 的
commit，因為有時 PR 合併後 branch 上仍會繼續開發。

## 用 worktree 平行開發

[git worktree](https://git-scm.com/docs/git-worktree) 是接到同一個 repository、
位於自己 branch 上的第二個工作目錄。讓每個平行 agent 或任務在自己的 worktree
裡跑，它們的檔案編輯就永遠不會衝突。Claude Code 直接整合了這個機制
（[docs](https://code.claude.com/docs/en/worktrees)）：

- `claude --worktree <name>` 在新 branch 上建立
  `.claude/worktrees/worktree-<name>/`，預設以 `origin/HEAD` 為基底。
- worktree 是*全新*的 checkout，所以被 gitignore 的檔（如 `.env`）不會在裡面。
  repo 根目錄的 `.worktreeinclude` 檔會把它們複製進來——用 `.gitignore` 語法，
  且**只複製本身被 gitignore 的檔**。已追蹤 (tracked) 的檔（已 commit 的
  `.vscode/settings.json`）本來就在 checkout 裡，不該列進去。
- 把 `.claude/worktrees/` 加進 `.gitignore`，worktree 內容才不會在主 checkout
  顯示為未追蹤 (untracked)。

## Forge CLI：gh 與 glab

用平台 CLI 在終端機操作 pull/merge request——GitHub 用
[`gh`](https://cli.github.com/)、GitLab 用
[`glab`](https://gitlab.com/gitlab-org/cli)：

```bash
gh pr create --fill                     # glab mr create --fill
gh pr checks                            # 看 CI
gh pr merge --squash --delete-branch    # glab mr merge --squash --remove-source-branch
```

它們讓你在常見流程中不必開瀏覽器，也讓 PR 狀態可腳本化 (scriptable)。把它們
當作建議的便利工具，而非硬性依賴——即使少了 CLI，好的工作流用純 `git` 仍能
運作。

## 套件的 tag 驅動版本

當一個 repository 本身*就是*一個套件時，別把版本字串維護在三個地方
（`__init__.py`、`pyproject.toml`、以及 git tag）任其漂移 (drift)。讓 **git
tag 成為單一事實來源 (single source of truth)**。Python 方面，
[Packaging 指南](https://packaging.python.org/en/latest/discussions/single-source-version/)
建議由 VCS 推導版本：

- **setuptools** backend → [setuptools-scm](https://setuptools-scm.readthedocs.io/)。
- **Hatch / hatchling** backend → [hatch-vcs](https://pypi.org/project/hatch-vcs/)。

以 `vX.Y.Z` 打 tag（去掉 `v` 後需與 PEP 440 相容），推送 tag，build 就會蓋上
對應的版本。release 流程變成：落地 release commit → `git tag -a vX.Y.Z` →
推送 tag。

## 來源

- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [Claude Code worktrees](https://code.claude.com/docs/en/worktrees)
- [git-worktree docs](https://git-scm.com/docs/git-worktree)
- [Python Packaging — single-sourcing the version](https://packaging.python.org/en/latest/discussions/single-source-version/)
- [setuptools-scm](https://setuptools-scm.readthedocs.io/) ·
  [hatch-vcs](https://pypi.org/project/hatch-vcs/)
