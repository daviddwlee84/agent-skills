# 實作 Python 版本／發布規範與 PR-safe release ownership（#40、#41）

## Context

依據 `.specstory/references/chatgpt-版本發布管理想法-20261102-0053.md`，解決平行 feature agents 提前占用正式版本與 repository-global tags，造成合併順序不同時版本倒退、squash 後 tag 不在 main 歷史上的問題。

- **#40**：`pyproject.toml` 預設單一版本來源、pre-1.0 相容性政策、changelog scaffold、發布驗證、下游 pinning。
- **#41**：讓 Python／Git skills、生成的 agent instructions 與可選 CI checks 對 feature PR、main、release 有一致的權限邊界。
- **已確認可保留**：現有純 Python scaffold 使用 Hatchling + 靜態 `[project].version`；`__init__.__version__` 已讀取 `importlib.metadata`，CLI／API 也重用它。Rust profile 使用 maturin，不應改成 Hatch。
- **主要缺口**：沒有 changelog 或 release verification；版本測試僅檢查非空；Justfile 有未驗證的 `publish`；Git skill 仍普遍推薦 VCS 版本與 force-retag 修復。

### Skill intent

- 功能：引導／生成具有明確發布權限與版本一致性檢查的 Python 專案。
- 觸發：Python scaffold／modernization、version/changelog 調整、發布準備、平行 PR 開發。
- 產出：更新既有 skills、references、project templates、驗證 helper 與回歸測試。
- 可驗證：生成結果、Git 歷史 fixtures、wheel/sdist 安裝版本比對、lint 與現有 quality gates。

## 1. 統一預設政策

| 情境 | 允許／責任 |
|---|---|
| Feature PR | code、tests、`[Unreleased]`；不自行修改 distribution version、建立正式 release heading、tag 或發布套件。CI 可建置不發布的驗證產物。 |
| Main | 整合 PR，merge 不等於 release；版本轉換由 release owner 管理。 |
| 明確授權的 release 流程 | 決定版本、finalize changelog、驗證指定 main commit、建立 immutable annotated tag，經授權才發布。 |

- 新 scaffold 從 **`0.1.0.dev0`** 開始，保留 `[project].version` 為唯一 Python package 版本來源。開發 placeholder 不保留下一個正式版本號。
- **預設 pre-1.0 政策**：breaking change 升 minor；相容功能／修正升 patch。專案既有明文政策優先；Conventional Commits 是版本選擇的輸入，不是無條件 `feat → minor`／`breaking → major`。
- Static lifecycle：main-owned `.dev0` → 授權 release-preparation PR 決定實際正式版本 → merge／release → release-owned follow-up 切回下一個 `.dev0`。必要時更新 lockfile、重新安裝 metadata。
- 既有 Hatch path-based static source、`hatch-vcs`／`setuptools-scm` 均可保留；不強制遷移，也不並存兩個手動版本來源。說明 PEP 440 preview identity、editable metadata 可能過期，以及 VCS 的 full-history/tags、sdist、dirty/local build 限制。
- 現有 tags 一律不自動移動、刪除或重用；先調查 ancestry、已發布 artifacts 與下游，再決定新版本遷移。

## 2. 更新既有 skills 與發布 runbook

### Python skill

主要檔案：
- `skills/local/python-project-best-practice/SKILL.md`
- **新增** `references/versioning-and-releases.md`
- `references/uv-and-pyproject.md`、`agent-interface.md`、`quality-gates.md`

在 SKILL 加入短版 **Release ownership**、具體 release/versioning trigger、gotchas 與條件式 reference routing，保持低於 500 行。詳細 packaging 政策集中在新的 reference；Git tag/provenance 規則交叉連結到 Git skill，不複製整份規範。

Runbook 是預設的單一 maintainer-operated release 入口：
1. 明確取得發布授權，整合 release-preparation PR。
2. Fetch main/tags，不 force；記錄獲准的 main release SHA，以該 SHA 的乾淨 checkout 操作。
3. 先檢查 lock，再跑 quality gates 與 artifact verification。
4. 確認目標 tag 在本地與 remote 均未使用，annotated tag 明確指向記錄的 SHA，再驗證 tag。
5. 只推該 tag；發布時只使用同一批已驗證 artifacts，禁止臨時重建或把舊 `dist/*` 一起上傳。
6. 完成 release-owned 的下一輪開發版本轉換。

在 `uv-and-pyproject.md` 加 branch／main／release command matrix，移除無上下文的 bump/publish 指令。下游應用／工具使用明確 release pin + lock；未發布實驗用完整 commit SHA，更新透過可 review 的依賴升級。區分 consumer pins 與 reusable library dependency ranges；修正一次性 `uvx --from` 的 floating-ref 範例，不擴大重構整套 dependency policy。

### Git skill

同步 `skills/local/git-workflow/SKILL.md` 與 references：
- `versioning-and-releases.md`：main-centered、release-on-demand、static default／VCS opt-in、immutable tags。
- `worktrees-parallel-agents.md`：tags 共享、不保留正式版號，以及兩個歷史回歸案例。
- `conventional-commits.md`：版本 bump mapping 必須服從 pre-1.0／repo policy。
- `project-tiers.md`：保留既有 tiers，澄清 integration／deployment 不自動代表 Python package release。

移除 force-retag 作為一般修復步驟的建議。

## 3. 讓規則進入生成專案

修改 `skills/local/python-project-best-practice/assets/project/`：
- `pyproject.toml.tmpl`：初始版本 `.dev0`，不更換 backend。
- **新增 `CHANGELOG.md.tmpl`**：只有 `[Unreleased]` 與 Added／Changed／Fixed／Breaking Changes 分類，不捏造正式發布紀錄。
- `AGENTS.md.tmpl`：加入 ownership、0.x 政策與 release runbook 指引，置於自動生成的 CLI block 之外。
- `README.md.tmpl`、`scripts/README.md.tmpl`：發布步驟、驗證命令、下游 pinned install；說明示範 tag 必須先正式存在。
- `Justfile.tmpl`：保留一般 `build`，增加 verification recipes；**移除沒有檢查的 `publish` recipe**。預設不生成自動發布 workflow。
- `tests/test_core.py.tmpl`、`test_cli.py.tmpl`、`test_api.py.tmpl`：從非空／key 存在改成實際 metadata／runtime／CLI／API equality。
- `rust/Cargo.toml.tmpl`：內部 extension crate 標示 `publish = false`；其 crate version 不是 Python distribution 的第二個權威來源，以 maturin build 測試確認不要求兩者相等。

重用 `scripts/new-python-project.py` 的 `load_manifest()`／`check_manifest()`、`wanted()`、`apply_markers()`、`render()`，所有新模板登錄 `assets/manifest.toml`。新 repo 明確 `git init -b main`；保留 `--no-git`、`--dry-run` 與 `CLAUDE.md → AGENTS.md` symlink 行為。

## 4. 加入精簡、只驗證不發布的 helper

新增共享模板 `assets/project/scripts/verify_release.py.tmpl`，提供兩個清楚分離的 mode：

- **`pr --base SHA --head SHA [--release-intent]`**：比較 merge-base 到 PR head，避免 main 已推進造成誤判。一般 PR 禁止 version 變更、新增正式 release heading／finalization；允許 Unreleased 與其他正常 pyproject 修改。明確 release intent 驗證合理的 release-preparation 或 post-release `.dev0` 轉換，不能直接略過所有檢查。
- **`release --version VERSION --commit SHA --main-ref REF [--tag TAG] --output DIRECTORY`**：驗證指定 SHA、乾淨 checkout、release-line ancestry、static version／dated changelog／lock 一致。帶 tag 時要求 annotated tag 的 peeled commit 等於指定 SHA，tag version 一致。main 在驗證期間往前推進，不應偷偷改用新 SHA。

Artifact verification：
- output 必須是新的獨立目錄；不刪除／覆蓋既有 artifacts。
- 以既有 backend 建 wheel + sdist，核對 distribution name／version。
- 在 source tree 外的新 venv 非 editable 安裝，清除 source-path 影響，比對 installed metadata、`__version__`、CLI info JSON，以及適用的 API/OpenAPI version；拒絕 `0.0.0+unknown` fallback。
- 安全解開本次 sdist 到另一個新目錄，重建 wheel 並重做安裝 smoke checks。
- 回報 release SHA、artifact paths／hashes；不 bump、不改 changelog、不 tag、不 push、不 publish。

Helper 以新 scaffold 的 static-source contract 為範圍，不實作通用 backend/versioning framework；既有 dynamic/VCS 專案使用文件化 backend-specific 流程，不能假裝已被此 checker 支援。使用現成 toolchain／標準 library，必要外部依賴以 PEP 723 宣告。提供 `--help`、JSON stdout、可操作 stderr、明確 exit codes；驗證不修改 tracked files。

**CI guardrails 採 opt-in 範例**，放在 release reference：
- PR job 只有 read permissions，正確 fetch base/head history，不使用 `pull_request_target` 執行未信任程式。
- `--release-intent` 只是檢查模式，不是授權；branch name、label 或 PR 自帶 flag 都不能單獨授予 release 權限。release 例外須由 maintainer-controlled／受保護流程選用。
- 說清楚 CI 只能發現違規，不能阻止 tag push；真正限制依靠 tag rulesets、最小權限與 protected publishing environment。
- 一般 CI 不持有 publishing credentials，也不因 merge 自動發布。

## 5. 回歸測試與文件同步

新增 `skills/local/python-project-best-practice/tests/`，使用 stdlib unittest、temporary repos 與 isolated Git config。重用鄰近測試模式：
- `skills/local/zensical-site-bootstrap/tests/test_site.py`：scaffold fixture、snapshot/no-write、integration 分層。
- `skills/local/nautilus-trader/tests/test_nautilus_trader.py`：local remotes、annotated tags、peeled SHA。

必要案例：
1. 六種 profiles 正常 render，manifest 一致、無殘留 placeholder、初始 `.dev0`、changelog、symlink 與 main 初始化正確。
2. 兩個 worktrees 的 feature PR 任意順序合併，包括跨 release transition：不分配正式版號、不倒退 main 的版本；正常處理 changelog conflicts。
3. Feature stable bump／finalized heading 被拒絕；明確 release／post-release transition 可通過，但不产生 tag／publish。
4. Feature commit 曾 tagged 再 squash：保留舊 tag 的原 OID，不能拿它驗證新的 main release；改用下一個未使用版本。
5. Wrong/lightweight tag、錯誤 commit、重複版本、dirty tracked files、缺失／不一致 changelog、stale artifacts、metadata/runtime mismatch 均失敗。
6. 真實 wheel install + sdist rebuild，包括 CLI／API 與 Rust/maturin；驗證非 source-tree import 假陽性。

`Makefile` 新增 fast fixture 與 integration targets；`.github/workflows/validate.yml` 加入對應測試，將需要 dependencies／Rust toolchain 的 smoke checks 分開。保留 `make validate` 原本 portable publish-gate 語意。全 profiles 執行實際生成後的 quality checks；不把 render 成功冒充 runtime 測試成功。

同步既有雙語頁面：`docs/skills/python-project-best-practice{,.zh-TW}.md`、`docs/skills/git-workflow{,.zh-TW}.md`、`docs/reference/git-workflow{,.zh-TW}.md`。不修改 catalog／nav／marketplace。Audit script 維持原範圍，不宣稱它已新增 release auditing。

## Verification

實作完成後執行：
- 新增的 `make test-python-project-skill`（fixtures）與 `make test-python-project-integration`（真實 artifact/profile checks）。
- 六種 disposable profiles：`uv sync`、有 CLI 者 `just docs-sync`、`just lock-check`、`just check`、`just cov`，以及新的 release verification。
- `GIT_CONFIG_GLOBAL=/dev/null /bin/bash skills/local/git-workflow/tests/test_check_commit_msg.sh`。
- 對兩個修改的 skills 執行 `skills/local/skill-author/scripts/lint-skill.sh`。
- `make validate`、`make docs-build`、`git diff --check`。
- 測試只在 synthetic repos 建 local tags；禁止真實 push／publish。任何環境缺依賴、測試失敗或跳過都如實回報。

## 執行與範圍界線

- 核准後用 `skills/local/forge-native-dev/scripts/forge-worktree.sh start 40` 建獨立 worktree；#40/#41 修改同一套 contract，作為一組 cohesive change，後續 PR 同時連結兩者。
- `td usage` 現在因沒有 database 而失敗；實作開始時初始化 local tracking，執行 `td usage --new-session -q` 與 start/log/handoff/review。review 必須如實註明執行者。
- 保留目前未追蹤的 SpecStory transcripts／參考對話。
- 不修改 QDK 或 `qdk config edit`、不新增 skill／discovery links、不改 repository 自己 docs-only pyproject 的版本。
- 本次先完成檔案修改與驗證；commit、push、建立／合併 PR、正式 release 與關閉 GitHub issues 另依授權處理。目前只有計畫檔變更，尚未執行實作或測試。
