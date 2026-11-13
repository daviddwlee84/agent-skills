# 擴充 `superproject-workspace`：從零建立、任務 worktree、repair、pointer-only home repo

## Context 背景

使用者想把「Home Repo / submodule superproject」的建立與維護做成 skill（外層怎麼稱呼、是否固定在 `main`、child worktree 怎麼開與收尾）。調查結果：

- 本 repo **已有** `skills/local/superproject-workspace`（PR #34，v0.2）：涵蓋 per-child policy（`x-policy track|pin|lazy`）、`status/init/pull/bump/preflight/worktree/audit/adopt/ci-plan`。
- 它缺四項能力，也是這次要補的：
  1. 從零建立與新增 child（目前 `find_root` 沒有 `.gitmodules` 就失敗，沒有 `new`/`add`）。
  2. 跨 child 的任務 worktree（目前一次只能處理一個 child）。
  3. orphan worktree 偵測與修復，以及防止從「外層 linked worktree 內的 child」開 worktree（這會在外層 worktree 被刪時讓所有 child worktree 一起壞掉，是實際發生過的故障）。
  4. 不使用 submodule 的 pointer-only home repo 模式（Matt Pocock 原版；目前只在 decision guide 提到）。

**使用者已決定（不要重新討論）**

1. 擴充既有 skill，不另開新 skill。
2. 這是**通用、對外發布**的 skill：skill 本體、tests、assets、docs 內不得出現維護者個人的 repo 名、org 名、個人路徑，也不得依賴個人工具。
3. 能用 submodule 時仍**推薦 submodule**（外層 pin 住 child 版本）；pointer 模式是退路，decision guide 要寫明判斷標準。
4. child worktree 位置改為可設定，**預設維持** repo 內的 `.worktrees/<child-path>/<branch-slug>`。
5. `dev` CLI 的相容性是另一個 repo 的後續工作，本計畫只附建議（見最後一節），**不實作**。

**我採用的預設（核准時可改）**

- 任務 worktree 用 task-first 佈局：`<root>/_tasks/<task>/<child>`。
- 設定與 pointer manifest 放在 root 的 `.superproject`（git-config 語法，用 `git config -f` 讀寫，不需 TOML）。
- pointer child 預設路徑為 root 內、gitignored 的 `repos/<name>`；`../x`、`~/x`、絕對路徑仍可用。
- assets 內指向本 skill 發布來源的 raw URL 保留（它是 skill 自己的來源，可用 `SUPERPROJECT_CLI` 覆寫），不視為個人資訊。

所有 skill 路徑以 `skills/local/superproject-workspace/` 為基準。實作前先完整讀過：`SKILL.md`、`references/*`、`assets/*`、`scripts/superproject.py`、`tests/test_superproject.py`，以及 `skills/local/skill-author/references/script-design.md`、`this-repo-conventions.md`。下列行號來自規劃時的讀取，動手前請以實際檔案為準。

---

## 現有程式碼中會影響設計的事實

- `find_root`（`superproject.py` 約 L139-156）三個分支都要求 `.gitmodules`；`main`（約 L1060-1070）對每個子指令都呼叫它。
- 狀態已經是從 checkout 本身推導（`is_initialized` 約 L196-201 用 `.git` + `rev-parse --show-toplevel`），沒有用 `git submodule status`，這點不用改。
- 但 `.git` 檔指向不存在的 gitdir 時會被當成「未初始化」，`cmd_init`（約 L371-393）就會對有內容的目錄跑 `submodule update --init`。需要第三種狀態。
- `root / s.path` 出現約十一處（約 L135, 197, 241, 282, 399, 468, 508, 512, 533, 646, 871），對 `../x`、`~/x` 會錯。
- worktree 根目錄寫死在 `WORKTREE_DIR`：`wt_path`（L614）、`ensure_gitignore`（L618-627）、`list_child_worktrees`（L283、L296）、`cmd_audit`（L769）。
- `cmd_audit` 約 L709-710 的 `no-submodules` 要改成「沒有宣告任何 child」。
- **維持單一檔案 CLI**（recipes、hook、CI 都以單檔 `uv run --script` 執行，`adopt --vendor-cli` 也只複製一個檔）。拆的是 tests，不是 CLI。

---

## Design 設計

### 共用基礎

**`.superproject`**（root，git-config 語法）：沒有 `.gitmodules` 時的 root 標記，並存放 workspace 設定與 pointer child。

```ini
[workspace]
    mode = submodule            # submodule | pointer：`add` 的預設種類
    worktree-root = .worktrees  # 相對 root、絕對路徑或 ~
    map-file = docs/repos.md    # 選填：完整 repo map 的輸出位置
[repo "docs-site"]              # pointer child
    path = repos/docs-site
    url = git@example.com:org/docs-site.git
    branch = main
    x-tier = reference
    x-role = Public documentation site
```

- worktree root 優先序：`git config --local superproject.worktreeRoot`（每個 clone 各自、不進版控）> `.superproject` 的 `workspace.worktree-root` > `.worktrees`。
- `.gitmodules` 新增 key `x-role`（一行用途說明，供 repo map 使用）。

**新 helper**

| Helper | 行為 |
|---|---|
| `child_dir(root, s)` | `expanduser` 後，非絕對路徑則相對 root。取代所有 `root / s.path`。 |
| `worktree_root(root)` | 套用上述優先序。 |
| `display_path(root, p)` | 在 root 內顯示相對路徑，否則絕對路徑。 |
| `wt_key(s)` | submodule 用 `s.path`，pointer 用 `s.name`。 |
| `git_dirs(repo)` | 由 `git rev-parse --absolute-git-dir --git-common-dir` 取得 `(git_dir, common_dir)`；第二個若為相對路徑則對 `repo` 解析。不要用 `--path-format`。 |
| `checkout_state(root, s)` | `ok` / `absent`（無目錄或空目錄）/ `broken`（有 `.git` 但 rev-parse 失敗或 toplevel 不符）/ `foreign`（非空且無 `.git`）。`is_initialized` 改為 `== "ok"`。 |

**模型**：`Sub` 加 `kind`（預設 `submodule`）與 `role`；`eff_policy` 對 pointer 回傳 `"pointer"`；`load_subs` 改成通用的 `_load_cfg(root, file, section)`，分別讀 `(.gitmodules, submodule)` 與 `(.superproject, repo)`。

**root 探索**：root 是含 `.gitmodules` 或 `.superproject` 的目錄。`find_root` 順序為 `--root` → `$SUPERPROJECT_ROOT` → 既有兩個 `rev-parse` 候選 → **新步驟** → 既有的往上走。新步驟：取 cwd 的 common dir，若符合 `<X>/.git/modules/...` 則 root 為 `X`；若符合 `<X>/.git/worktrees/<id>/modules/...` 則 root 為 `<X>/.git/worktrees/<id>/gitdir` 所指路徑的上層。這讓外部 worktree root 下的 child worktree 也能找回 root。`main` 中，subparser 設 `needs_root=False`（只有 `new`）時跳過 `find_root`。

**外層 repo 規則**（寫進 SKILL.md「Outer repo rules」、兩份 agents-block template、`references/agent-entry.md`）：

1. 稱為 *superproject*（submodule 模式）或 *home repo*（pointer 模式）；不要稱 monorepo、meta-repo、agent repo。
2. 外層停在 default branch。跨 repo 的功能放在 child branch；外層只有短命的「純外層內容」branch 與 CI bump branch。
3. 不為了 child 的工作替外層開 worktree，包含在 root 執行 `claude --worktree` 與 `isolation: worktree` 的 subagent。
4. child 先 commit 並 push，再用**一個**外層 commit 涵蓋所有受影響的 gitlink。
5. helper 不會自動 commit 或 push。
6. 進入 child 後以 child 自己的指示檔為準。

對應的新 audit finding：`outer-branch`（info）、`superproject-worktrees`（見 repair 一節）。

### (a) `new` 與 `add`

**`new [DIR] [--mode submodule|pointer] [--worktree-root PATH] [--no-agents --no-justfile --no-gitignore --no-git-config] [--dry-run] [--json]`**

- DIR 預設 cwd；不是 repo 才 `git init`。
- 拒絕：DIR 在別的 repo 的工作樹內，或已是 root（提示改用 `adopt`）。
- 寫入 `.superproject` 的 `[workspace] mode`，然後跑與 `adopt` 相同的 scaffolding：把 `cmd_adopt` 約 L887-936 抽成 `scaffold(root, args, actions)` 共用。
- 不 commit。輸出 `{"root","mode","actions":[...],"dry_run"}`。

**`add URL [PATH] [--name N] [--pointer|--submodule] [--policy track|pin|lazy] [--bump pr|direct|manual] [--tier T] [--branch B] [--role TEXT] [--ref REV] [--no-clone] [--dry-run]`**

- 種類預設取 `workspace.mode`；PATH 預設為 URL basename（去 `.git`），pointer 預設 `repos/<name>`。
- 拒絕：name/path 與既有 child 的 name、path 或 `wt_key` 衝突；目標存在且非空（submodule 種類）；`.gitmodules` 有未 stage 的修改；root 是 linked worktree；`wt_key` 第一段為 `_tasks`。
- submodule 種類：`git submodule add [--name N] [-b B] -- URL PATH` → 寫 `x-policy`（預設 `pin`）、`x-bump`、`x-tier`、`x-role`，`lazy` 另寫 `update = none` → `branch` 未設且非 lazy 時取 child 的 `origin/HEAD` → 有 `--ref` 則 `checkout --detach REV` 並 `git add PATH` → `git add .gitmodules`。不 commit。
- pointer 種類見 (d)。完成後重新 render repo map。
- 不在範圍：把既有的 embedded repo 收編成 submodule（拒絕並提示 `absorbgitdirs`）、`remove` 子指令（在 `gotchas.md` 給手動步驟）。

**`init` 強化**：`ok` 一律跳過，結果加 `head`、`recorded`、`drift`；`broken` / `foreign` 回報 `refused`、exit 1 並指向 `repair`，絕不對其執行 `submodule update`。`--recursive` 說明改為只套用於這次初始化的 child 的 nested submodule。

**`audit` 新增**：`submodule-config-missing`（info；checkout 正常但 `.git/config` 沒有 `submodule.<name>.url`）、`checkout-broken`（error）、`agents-not-loaded`（warn；`AGENTS.md` 與 `CLAUDE.md` 並存，`CLAUDE.md` 既非 symlink 也沒有 `@AGENTS.md`，而 managed block 只在 `AGENTS.md`）。

### (b) 任務 worktree

**佈局**（`R` 為 worktree root，預設或自訂皆同）：

- 單一 child（不變）：`R/<wt_key>/<branch-slug>`
- 任務：`R/_tasks/<task-slug>/<wt_key>`

任務目錄鏡射 superproject 的相對佈局，成員間的相對路徑仍可解析，且可把一個目錄整個交給 editor 或 agent。`_tasks` 為保留名。

**不使用 state 檔**：以每個 child 的 `git worktree list --porcelain` 為準；路徑落在 `R/_tasks/<t>/` 下即屬於任務 `t`。

**重構 `list_child_worktrees`**：回傳 child 的所有 linked worktree，加欄位 `abs_path`、`path`、`managed`（是否在 `R` 下）、`task`、`untracked`、`unpushed`（`rev-list --count @{upstream}..HEAD` 或 null）。既有呼叫端以 `managed` 過濾。

**指令**

- `task open TASK CHILD... [--branch B] [--base CHILD=REV]... [--no-fetch] [--dry-run]`
  - TASK 以 `git check-ref-format --branch` 驗證；branch 預設等於 TASK。
  - base 規則沿用既有（約 L668-676）；pointer 用 `origin/<branch>`。
  - idempotent（已存在的成員回報 `exists`）。
  - 兩階段：先對所有 child 做 precheck（狀態 ok、通過 guard、目標可用），再建立。中途失敗時，用 `git worktree remove` 與 `branch -D` 回滾**本次**建立的項目並 exit 1。
- `task list [TASK]`：每個成員回報 `child, kind, path, branch, head, dirty, untracked, unpushed, merged, prunable`，任務層有 `stray_dirs` 與 `ready_to_close`（全部乾淨且已 merge）。
- `task close TASK [CHILD...] [--delete-branch] [--force] [--dry-run]`
  - 先檢查全部成員；任一有 tracked/untracked 修改，或加 `--delete-branch` 時有未 merge 者，整組拒絕（除非 `--force`）。
  - 然後逐一 `git worktree remove`、選擇性 `branch -d`、`rmdir` 空的上層到 `R`。**絕不 `rm -rf`**。
  - 結尾提示：`pull`，再 `bump <members> --commit`。

**`worktree` 的變更**：`add` 使用 `worktree_root` 並加 guard；`list` 加 TASK 欄與 `--all`（含非 managed）；`remove` 會 `rmdir` 空上層。`ensure_gitignore` 與 audit `worktrees-not-ignored` 只在 `R` 位於 root 內時作用。新 audit info `worktree-outside-root`。抽出 `plan_worktree(root, s, branch, target, base)` 給 `worktree add` 與 `task open` 共用。

### (c) guard、orphan 偵測、`repair`

**Guard** `assert_durable_store(root, s)`，由 `worktree add`、`task open`、`add`、`repair --reattach` 呼叫：

```
root_gd, root_cd = git_dirs(root); _, child_cd = git_dirs(child_dir)
root_linked = root_gd != root_cd
refuse if child_cd.is_relative_to(root_cd / "worktrees")
       or (root_linked and child_cd.is_relative_to(root.resolve()))
```

拒絕訊息指出 main checkout 的路徑並要求在那裡重跑；沒有 override flag。

**偵測** `scan_health(root, subs)`，`audit` 與 `repair` 共用：

| Code | 判定 | 等級 |
|---|---|---|
| `worktree-prunable` | porcelain 區塊含 `prunable` | info |
| `worktree-relinkable` | `R` 下的目錄有 `.git` **檔**且其 `gitdir:` 目標不存在，但對應 child 的 `<child_cd>/worktrees/<basename>` 存在 | warn |
| `worktree-orphan` | 同上但無對應 admin dir。目標含 `/worktrees/<x>/modules/` 時 `cause = "superproject-worktree-removed"`，否則 `"store-missing"` | error |
| `worktree-at-risk` | admin dir 符合 `<root_cd>/worktrees/*/modules/**/worktrees/*` | warn |
| `superproject-worktrees` | 外層有 linked worktree；任一含已初始化的 `modules/` 則 warn，否則 info | info/warn |
| `stale-submodule-config` | `.git/config` 的 `submodule.<n>.*` 不在 `.gitmodules` | info |
| `stale-module-store` | `<root_cd>/modules` 下含 `HEAD` 的目錄不在 `.gitmodules`（不要往 store 自己的 `modules/` 下鑽） | info |

掃描時走訪 `R`，遇到含 `.git` 的目錄就不再往下，並依兩種佈局對應回 child；對應不到的回報 `child: null`。

**`repair [--prune] [--reattach [--base REV]] [--delete-orphans] [PATH...] [--dry-run] [--json]`**

| 呼叫方式 | 可以做的事 |
|---|---|
| 無 flag | 只做無損動作：對每個 `worktree-relinkable` 執行 `git -C <child> worktree repair <dir>` 並用 `rev-parse` 驗證。其餘只列出，並註明哪個 flag 會處理。 |
| `--prune` | `git -C <child> worktree prune`，以及 `git config --remove-section submodule.<n>`。不動工作檔與 store。 |
| `--reattach` | 把 orphan 的檔案重新接回 child 的正式 store（步驟如下）。不改動工作檔。 |
| `--delete-orphans PATH...` | 必須明確指定路徑，且掃描結果確認為 orphan。`--dry-run` 印出檔案數與最新 mtime。這是唯一會刪目錄的步驟。 |

Reattach 步驟（**尚未驗證，必須由測試證明**）：過 guard → `git -C <child> worktree add --no-checkout -b rescue/<dirname> <tmp> <base>`（`<tmp>` 為同層暫存目錄）→ 由 `git -C <tmp> rev-parse --absolute-git-dir` 取得 admin dir `A` → 把 `<orphan>/.git` 寫成 `gitdir: A`，把 `A/gitdir` 寫成 `<orphan>/.git` → 移除 `<tmp>/.git` 並 `rmdir <tmp>` → `git -C <orphan> reset -q`。base 預設為 gitlink（submodule）或 `origin/<branch>`（pointer）。文件要說明：orphan 上未 push 的 commit 已隨 store 消失，檔案會顯示為修改。

**若 reattach 在測試中不可靠**：保留偵測，把 reattach 改成 `references/repair.md` 的手動步驟，不出貨該 flag。

**永不自動執行**：刪除任何 `.git/modules/*` store、強制移除有修改的 worktree、搬移 worktree、處理 `worktree-at-risk`（只給步驟：push branch → remove → 回 main checkout 重開）。

輸出 `{"findings":[...],"actions":[...],"remaining":n}`；仍有 error 等級 finding 時 exit 1。

### (d) pointer-only home repo

pointer child 是 `.superproject` 的 `[repo "<name>"]` 區段，載入同一個 `Sub` 清單（`kind="pointer"`）；同一個 repo 可兩種並存。絕對路徑會有 audit info `pointer-path-absolute`。

| 指令 | 對 pointer 的行為 |
|---|---|
| `add --pointer` | 寫入區段；除非 `--no-clone` 否則 clone；若目標已有 clone 且 `origin` URL 相符則就地收編；路徑在 root 內時加 gitignore。 |
| `init` | `git clone [--branch B] URL DIR`，只在被點名、`--tier` 選到或 `--all` 時（按需 clone）。`foreign` 拒絕。 |
| `status` | POLICY 顯示 `pointer`，GITLINK 顯示 `-`，LAG 為 HEAD 落後 `origin/<branch>` 的數量。JSON 加 `kind`；頂層 key `submodules` 保留以相容。 |
| `pull` | 被點名時 ff-only，不需 `--force`（改約 L403 的檢查）。 |
| `bump` / `preflight` / `ci-plan` | 排除；點名時拒絕並說明 pointer 沒有 gitlink，要 pin 請用 submodule。 |
| `worktree` / `task` / `repair` | 與 submodule 相同，store 是 clone 自己的 `.git`。 |

選取條件新增 `--kind submodule|pointer`。pointer 的 audit code：`pointer-url-mismatch`（warn）、`pointer-not-ignored`（warn）、`pointer-tracked`（error）。

**Repo map**：第二個 managed block（`<!-- superproject-workspace:repo-map -->`），由 `render_repo_map(subs)` 對兩種 child 產生，每行含名稱、`x-role`、路徑、缺少時的指令、policy/tier。預設寫入 `find_agents_file` 回傳的檔案；設了 `workspace.map-file` 時，完整清單（依 tier 分組）寫到該檔，agents 檔只留一行指標與各 tier 數量（repo 很多時的 progressive disclosure）。`new`、`add`、`adopt` 都會更新。audit：`repo-map-stale`（warn）、`repo-map-large`（info，inline 超過 25 筆）。

`render_asset` 加 placeholder 替換（`{{WORKTREE_ROOT}}`）；沒有任何 submodule 時 `new`/`adopt` 使用新的 `assets/agents-block-pointer.md.template`。

`__version__` 升為 `0.3.0`。

---

## Documentation 文件變更

**`SKILL.md`**（目標 300 行內，lint 上限 500）

- `description`：涵蓋兩種模式與新能力，加入 "home repo" 及 zh-TW 觸發語（例如「開 home repo」「跨 repo worktree」）；含 `: ` 所以用單引號；**長度控制在 900 字元內**（超過 1024 無效），以 `lint-skill.sh` 確認。
- 新段落「Two modes」（推薦 submodule、pointer 為退路、連到 decision guide）與「Outer repo rules」。
- Workflow 加 step 0（從零建立 / 新增 child）、step 3b（一個任務跨多個 child）、step 7（Repair）。
- 改掉「When NOT to use」中把 pointer 模式排除的那條。
- Gotchas 新增：外層 linked worktree 會切斷 child worktree、在 root 執行 `claude --worktree`、不要在 root 跑 `git clean -ffdx`。
- 把含個人 repo 名的範例換成中性名稱（例如 `[submodule "core"] path = libs/core-engine`）。

**`references/`**

- `decision-guide.md`：開頭寫明「可行時優先 submodule」，加判斷表。選 submodule：需要重現某一組版本、外層內容引用 child 版本、有跨 child 的 CI。選 pointer：外層歷史不能或不想有 gitlink、child 已固定在磁碟其他位置、數十個很少動的 repo、協作者或工具無法處理 submodule、沒有人會 bump。並寫明 pointer 模式失去的東西（沒有 snapshot、`bump`、`preflight`）。
- `home-repo.md`（新）：manifest、root 內外路徑、按需 clone、repo map 與 `map-file`、外層與 child 各放什麼、harness 載入注意事項、pointer 轉 submodule。
- `worktrees.md`：可設定的 root 與取捨、任務佈局、guard、`list --all`、一小段「Environments」（約 15 行，無 CLI 支援：環境綁定路徑，root 的環境服務 pin 住的 checkout，worktree 或任務目錄自己建環境；不建議 `PYTHONPATH` 覆寫）。另加一句通用說明：若其他 worktree 管理工具建立了完整的外層 worktree，不要從裡面開 child worktree。
- `repair.md`（新）：以症狀開頭（`.worktrees/...` 內出現 `fatal: not a git repository`）、finding code、各 flag 的作用、at-risk 與 stale store 的手動步驟、為何 `rm -rf` 加 prune 不算清理。
- `agent-entry.md`：修正載入規則。Claude Code 只有在 cwd 及上層沒有 `CLAUDE.md` 時才讀 `AGENTS.md`；子目錄的 `CLAUDE.md` 在讀到該目錄檔案時才載入；`--add-dir` 的目錄需 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 才載入 `CLAUDE.md`，且永不載入 `AGENTS.md`；雲端 Projects 只載入各 repo root 的 `CLAUDE.md` 與 `.claude/rules`，不載入 `.claude/skills`。child 角色表與 project memory 放哪裡是選擇，預設為 agents 檔內的 repo map 與外層的 memory。
- `policies.md`：加 `x-role`；pointer 沒有 policy。
- `gotchas.md`：`ignore = dirty` 僅作為個別 child 的 opt-in（不要 `ignore = all`）、移除 child 後殘留的 config/store 與正確移除步驟、nested `--recursive`、`git worktree move` 不支援含 submodule 的 worktree。
- `case-patterns.md`：改寫為通用的模式描述，移除可辨識個人 repo 的內容。
- `ci-bump.md`：一句話說明 pointer child 不會出現在 `ci-plan`。

**`assets/`**：更新 `agents-block.md.template`（外層規則、任務行、`{{WORKTREE_ROOT}}`）；新增 `agents-block-pointer.md.template`；`justfile.snippet` 加 `sub-add`、`sub-task`、`sub-repair`。其餘三個不動。

---

## Tests 測試

**Fixture**（`tests/test_superproject.py`）：拆成 `BaseFixture`（tmp dir、gitconfig、`make_remote`、`commit`、`run_cli`、`json_cli`）與 `Fixture(BaseFixture)`；加 `linked_super(name)`（對 root 做 `git worktree add` 再 `submodule update --init app`）與 `sever(wt)`（`shutil.rmtree` 後在 root 跑 `git worktree prune`）。新測試檔：`test_setup.py`、`test_tasks.py`、`test_repair.py`、`test_pointer.py`。所有 fixture 使用中性名稱。

**新 case**

- setup：`test_new_creates_marker_and_scaffold`、`test_new_dry_run_writes_nothing`、`test_new_refuses_inside_existing_repo`、`test_add_submodule_stages_gitlink_and_policy`（staged 路徑剛好是 `.gitmodules` 與 child，HEAD 不變）、`test_add_refuses_duplicate_and_nonempty_target`、`test_add_lazy_sets_update_none`、`test_init_preserves_drifted_checkout`、`test_init_refuses_broken_checkout`、`test_status_initialized_without_git_config_entry`。
- worktree/task：`test_worktree_root_from_tracked_config`、`test_worktree_root_local_override`（外部 root 時不動 `.gitignore`，且能從裡面找回 root）、`test_worktree_add_refused_in_linked_superproject`、`test_task_open_creates_members_same_branch`、`test_task_open_is_idempotent_and_extends`、`test_task_open_rolls_back_on_failure`、`test_task_list_reports_dirty_and_merged`、`test_task_close_atomic_refusal_then_force`。
- repair：`test_audit_flags_superproject_worktree_and_at_risk`、`test_repair_detects_orphan_after_superproject_worktree_removed`、`test_repair_reattach_preserves_files`、`test_repair_relinks_after_superproject_move`、`test_repair_prune_only_with_flag`、`test_repair_delete_orphans_requires_explicit_path`（exit 2）、`test_audit_reports_stale_config_and_store`。
- pointer：`test_pointer_add_clone_status`、`test_pointer_init_on_demand_only`、`test_pointer_outside_root_and_worktree`、`test_pointer_bump_refused`、`test_repo_map_rendered_and_stale_detected`、`test_map_file_progressive_disclosure`。

**接線**（目前這個 skill 的測試沒有接進 Makefile 與 CI）

- `Makefile`：加入 `.PHONY` 與
  ```
  test-superproject-skill:
  	GIT_CONFIG_GLOBAL=$(TEST_GIT_CONFIG_GLOBAL) python3 -m unittest discover -s skills/local/superproject-workspace/tests -v
  ```
  （沿用其他 `test-<skill>-skill` target 的變數寫法。）
- `.github/workflows/validate.yml`：加一個步驟執行 `make test-superproject-skill`。

---

## Repo plumbing 其他要動的檔案

- `skills/.claude-plugin/marketplace.json`：`version-control` 群組加 tags `home-repo`、`multi-repo`，描述補上 superproject / home repo。**不要動 `NN-` 前綴。**
- `docs/skills/superproject-workspace.md` 與 `.zh-TW.md`：補 `new`/`add`、`task`、`repair`、pointer 模式。
- `docs/skills/index.md` 與 `index.zh-TW.md`：更新該列文字。
- `README.md`「What's in here」：補上目前缺少的 `superproject-workspace`。
- `docs/changelog.md` 與 `.zh-TW.md`（Unreleased）：註明既有導入者在重跑 `adopt` 前會看到 `managed-block-stale`。
- `skills/local/forge-native-dev/references/coexistence.md`：補 `_tasks/<task>/...`，並說明外層 issue worktree 只用於純外層內容、無法從中開 child worktree。
- `skills/local/git-workflow/references/worktrees-parallel-agents.md`：補 root 執行 `claude --worktree` 的警告、任務 worktree、`repair`。

---

## Milestones 里程碑

| 里程碑 | 範圍 | 驗證 |
|---|---|---|
| M0（PR 1） | `BaseFixture` 拆分；`child_dir` / `worktree_root` / `display_path` 重構（行為不變）；Makefile target；CI 步驟 | `make test-superproject-skill`（原 17 個全過） |
| M1（PR 1） | `.superproject`、`find_root`、`new`、`add`（submodule）、`checkout_state`、`init` 強化、新 audit code、SKILL.md step 0 | 同上，加 `python3 scripts/superproject.py new --help` |
| M2（PR 2） | 可設定 root、guard、`task open/list/close`、`worktree list --all`、`worktrees.md` | `python3 -m unittest discover -s skills/local/superproject-workspace/tests -p 'test_tasks.py' -v` |
| M3（PR 2） | `scan_health`、`repair`、audit 整合、`repair.md` | 同上，`-p 'test_repair.py'` |
| M4（PR 3） | pointer 種類、repo map、pointer template、`home-repo.md`、decision guide | `-p 'test_pointer.py'`，再跑完整 suite |
| M5（PR 3 或 4） | 其餘 references、description、assets、docs 頁、README、changelog、marketplace、cross-links、版本 0.3.0 | 見下方 |

每個 PR 結束時 `SKILL.md` 必須只描述已出貨的功能。

## Verification 驗證

每個里程碑照上表執行；M5 結束時整體驗證：

```bash
make test-superproject-skill
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/superproject-workspace
make validate
uv sync --extra docs && make docs-build
```

另外：

- **通用性檢查**：對 `skills/local/superproject-workspace` 與 `docs/skills/superproject-workspace*` grep 維護者的 repo 名、org 名、使用者名稱與家目錄路徑，結果必須為空。
- **手動 end-to-end**（在 scratchpad 的拋棄式目錄，使用本機 bare repo）：`new` → `add` 兩個 submodule child 與一個 pointer child → `status` → `task open demo <a> <b>` → 在兩個成員各 commit → `task list` → `task close demo --delete-branch` → `audit` 無 error。再做一次故障演練：建立外層 linked worktree、確認 guard 拒絕、手動製造 orphan，確認 `repair --dry-run` 正確分類。
- 這次**不**對四個真實 superproject 執行任何寫入；導入屬於既有的 `backlog/superproject-workspace-adoption.md`。

## 風險

1. `repair --reattach` 的 admin 檔改寫未經驗證；失敗時的退路已寫在 (c)。
2. 升級後所有已導入的 superproject 會回報 `managed-block-stale`，屬預期行為，changelog 需註明。
3. CLI 會成長到約 1,800 行；仍維持單檔。

## 附：`dev` CLI 後續建議（另一個 repo，不在本次實作範圍）

**衝突點**：`dev work start --submodule` 會建立外層的 linked worktree，並把 child 初始化在裡面；這正是本 skill 的 guard 會拒絕開 child worktree 的佈局。此外 `dev` 的「worktree 不放在其他 checkout 內」規則與本 skill 預設的 repo 內 `.worktrees/` 相反，而 `[submodules] init = "recursive"` 是否會略過 `update = none` 的 child 尚未確認。

**建議**

- **現在做（只改文件）**：兩邊都寫明一個任務只用一種模式：`dev` 的完整外層 worktree（直接在 child branch 上工作，不再開 child worktree），或本 skill 從主 checkout 開的 child / 任務 worktree。並記下 `git config superproject.worktreeRoot ~/Worktrees/<super>` 這個設定，讓 skill 的 worktree 符合 `dev` 的規則。
- **排成 `dev-cli` 的小 issue**：(1) 讓 `dev git submodule status`、retire 檢查能辨識登記在 `<super>/.git/modules/<name>/worktrees` 下的 worktree，並指向 `task close`，避免誤判或卡住；(2) 確認 recursive init 會略過 `update = none` 的 child。
- **暫緩**：`dev work start` 的原生模式（不開外層 worktree，直接用任務佈局），等任務佈局實際用過再決定。
