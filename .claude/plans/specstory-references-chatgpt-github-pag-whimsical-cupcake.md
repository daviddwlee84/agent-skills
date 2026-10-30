# GitHub Pages 文件框架與 skill：評估結論及落地順序

## Context

使用者有多個既有專案依賴 `mkdocs-site-bootstrap` 與 MkDocs plugins，想評估新專案是否改用 Zensical，以及是否應另建 skill。後續補充：理想是**英文完整提供給所有讀者與 agent，部分文章可用繁中自行閱讀**，而非永久只做單語站。

這次只做評估：已讀取現有實作並查核官方資料，**未修改技能、遷移站點、安裝套件、執行建置或操作遠端 Issue／部署**。

## 建議結論

**保留 `mkdocs-site-bootstrap` 作為「英文主站＋可選繁中」的現行方案；Zensical 先作有限試點，不直接取代舊 skill，也不因為是新專案就一律採用。** 未來若封裝 `zensical-site-bootstrap`，使用獨立 skill，不改變既有 skill 的語意與維護入口。

| 專案情況 | 建議 |
|---|---|
| 既有 MkDocs + Material，依賴 i18n／自訂 plugins／hooks | 維持 MkDocs 1.x，保留上限與 lockfile，按專案盤點後才遷移 |
| 新專案要英文為主，現在或近期會提供部分繁中 | 仍優先現有 MkDocs 方案，支援按需翻譯與 fallback |
| 新的單語 Python／CLI／一般工具文件，確定暫不需要內容多語 | 可作 Zensical 試點；不能將這個例外擴大成所有新專案的預設 |
| 本 repo 的文件站 | 暫不遷移：目前有完整雙語與兩階段 LLM 建置流程 |

### 目標語言契約：英文優先，不強迫全站雙語

- 英文是完整 canonical 內容與預設入口；介面預設英文。
- 有需要的頁面才提供 `foo.zh-TW.md`，不要求所有頁面都翻譯。
- 語言切換優先到同一文章的對應版本；缺少繁中時保留英文內容，不顯示空白 placeholder。
- `llms.txt`／`llms-full.txt`／預設 Markdown sidecars 維持英文，繁中頁保留正確的人類閱讀與複製來源。
- 開啟語言選項不等於同意自動翻譯；翻譯仍需明確要求。

**介面翻譯 ≠ 語言選單 ≠ 內容多語。** Zensical 可指定 UI 語言並設定 alternate links，但不會因此自動建立翻譯頁、同頁映射、fallback 或語系搜尋。

本 repo 的 `mkdocs.yml:35–48` 已配置英文預設、繁中及 `fallback_to_default: true`。實作時進一步查核更正：**`add-language.sh --no-stubs` 已可跳過全站翻譯 stubs**，不需要新增同名能力。但這個選擇不會持續記錄，`add-docs-page.sh` 仍會依語言設定建立 stubs；**存在的 placeholder 不能當成缺譯來回退**。後續模式應重用現有旗標並補持久化與增頁整合，而不是重造功能。

此按需翻譯建議針對下游專案，不撤銷本 repo 對已發布 catalog 頁要求英／繁中成對的規則。

GitHub Pages 仍適合這些站點。它提供靜態資源，建置時的 Python／Rust／Node 工具由 Actions 執行；**換文件引擎與換 hosting 是兩個獨立決策**。暫不增加第三個涵蓋所有框架的 routing skill，也不為這個需求改寫成 Node 生態。

## 截至 2026-10-30 的查核

ChatGPT 建議的大方向合理，但要把「可讀舊設定」與「完整相容舊工作流」分開。

- Zensical 最新 GitHub release 為 **0.0.73（2026-10-26）**。不能僅憑 `0.x` 判定不能使用，也不能把將來版本的承諾當成現有能力。
- **0.0.67（2026-09-30）已加入原生 `llmstxt` 與 Copy as Markdown**。這是比 repo 內 4 月評估明顯進步的地方。
- Zensical **不執行任意 MkDocs plugin，也不提供舊 MkDocs plugin API**；未列為支援的 plugin 設定可能被靜默忽略。`hooks` 不支援；`gen-files` 仍需外部生成等替代流程。
- 官方的介面翻譯與 `extra.alternate` 語言選單，**不能視為 `mkdocs-static-i18n` 的 suffix 內容、fallback、翻譯導覽及搜尋等價實作**。完整 i18n 工作流仍在 roadmap，這是此 repo 的主要遷移阻礙。
- Material 公告安全與重大修補維護到 **2027-05-05**。「先保留」不是承諾往後幾年都不必管；鎖版能防破壞性升級，不能代替安全維護。
- ChatGPT 提到的「2026-11-05 發布 Zensical 0.1.0」本次未取得足夠官方佐證；目前 roadmap 的 11 月 5 日 banner 指向 Studio 產品發布，**不把該日期當作 SSG 遷移依據**。

### 對照我們實際需要的功能

| 現有能力 | Zensical 判斷與驗收重點 |
|---|---|
| Material 風格、搜尋、常用 Markdown extensions | 有相容路徑；仍需驗證實際頁面、搜尋及 snippets／Mermaid 等代表性內容 |
| `llms.txt`、`llms-full.txt`、Markdown sidecars | 官方已支援原生 `llmstxt`；需驗證 sections、輸出完整性及 project Pages 子路徑 |
| `mkdocs-copy-to-llm` | 可考慮以 `content.action.copy` 取代「複製 Markdown」；不宣稱等價取代全部 Open-in-LLM 按鈕與自訂資產 |
| `mkdocs-static-i18n` | 目前不能承諾現有工作流等價，不自製多次 build 拼站來掩蓋缺口 |
| 現有兩階段 managed builder | 高度 MkDocs-specific；不搬到新 skill，也不只把執行命令換成 Zensical |
| Python API docs | `mkdocstrings` 有官方相容實作；如需 `gen-files` 等搭配，仍須另行驗證，不列入新 skill 首版基本契約 |

現有 skill 不只是 scaffold：`references/i18n-guide.md:187` 定義兩次 strict build，先驗證預設語言 LLM artifacts，再合併完整雙語 HTML，成功才替換 `site/`。這些既有專案的維護、修復與內容保護能力值得保留。

## 後續落地方案

### 第一階段：更新決策文件與舊 skill 的必要維護

1. 更新 `skills/local/mkdocs-site-bootstrap/references/mkdocs-2-and-zensical.md`：以本次查核取代 4 月資訊；分清 Markdown extensions 與 MkDocs plugins；刪除「pre-1.0 一律不能用」「再留兩三年沒有問題」等過度斷言。**遷移到 Zensical 不代表解除 MkDocs `<2` 上限**，兩者是不同工具鏈。
2. 修正 `references/docs-stack-recipe.md:13`、`scripts/init-docs-site.sh:393` 的依賴安裝範例：目前遺漏模板已有的 MkDocs／Material major 上限，包括 social extras 的提示。補一個提示輸出的回歸測試；不藉此升級或改寫下游專案。
3. 保留原有腳本、偏好、兩階段 builder、遷移修復入口與 regression tests；受控更新 patch／minor 和 lockfile，而非永久凍結目前版本。
4. 補上「英文完整、繁中按需」的選型與操作說明，明列現有 stub 流程限制。實作時已確認 `add-language.sh --no-stubs` 存在並通過 selective-translation fixture；不重造該功能。將持久化按需翻譯模式作為獨立後續實作（Issue #36）：在既有 namespace 記錄明確模式，`add-docs-page.sh` 只在要求翻譯時建立指定語言頁；沿用既有 `--lang` 入口。保持原有使用者預設行為，不自動刪除任何已存在的翻譯或 placeholder。

**優先落地第一階段的文件與依賴提示修正。按需翻譯模式、下列 Zensical 試點與新 skill，分開確認範圍後再實作，不綁成一次全量變更。** 按需模式需修改上述兩支 helper、`SKILL.md`、`references/i18n-guide.md`／`references/preferences-schema.md` 及相關測試；驗收包含缺譯時確實顯示英文、有繁中時切到繁中、英文 LLM 輸出不受影響。

### 第二階段（後續可選）：隔離小型 Zensical 驗證站

先以查核時版本 `0.0.73` 建立可重現的單語 fixture（英文或繁中均可），不要拿現有雙語站直接試換引擎。包含首頁、巢狀頁、圖片、程式碼、連結、snippets／tabs／Mermaid 等代表性內容。

必須驗證：

- `uv sync --locked --extra docs` 與 `uv run zensical build --strict` 能完成；lockfile 缺失或漂移應失敗。
- HTML 導覽、搜尋、anchors、圖片，以及 `https://owner.github.io/project/` 子路徑都正確。
- `llms.txt`、`llms-full.txt`、Markdown sidecars 的內容與 sections 完整，連結保留 project 子路徑；不能只檢查檔案存在或 CLI exit code。
- 瀏覽器實測 Copy as Markdown，確認 snippets 等生成內容是否符合預期；原生功能未覆蓋舊 copy-to-LLM 的部分要明列差異。
- 前置盤點辨認 unsupported／unknown plugins、hooks、自訂 theme 等；遇到未知相容性先停止並報告，不依賴上游靜默忽略。
- 初始化 dry-run、既有內容保護、重跑衝突處理，以及失敗不發布壞 artifact 的流程。

**通過後才考慮第三階段；不通過則留在評估狀態，不用自製 i18n 或複製舊 two-pass builder 來勉強補齊。** 單語試點通過也不代表能滿足使用者的通用需求：必須另行證明上述「英文主站＋部分繁中＋缺譯回退」契約，Zensical 才能升格為一般新專案預設。本次沒有執行這些測試。

### 第三階段（後續可選）：封裝獨立、有限範圍的新 skill

新增 `skills/local/zensical-site-bootstrap/`，依 `skill-author` 慣例建立：

- `SKILL.md`：適用於明確選擇 Zensical 的單語新案；未指定框架時先依需求分流。偵測既有 MkDocs 依賴、設定和偏好，不能自行遷移。
- 最小初始化／本機預覽／建置／增頁導覽／LLM 輸出／CI 指引與必要 assets、scripts、tests。先檢驗上游 `zensical new` 可重用的部分，不重造不必要的 scaffolding；不可假設它會保護既有內容。
- 使用獨立 `zensical_site_bootstrap` 偏好 namespace。新 skill 必須能獨立安裝，不能假設 sibling MkDocs skill 的腳本存在。
- 優先使用原生 llmstxt 與 `content.action.copy`，不帶入舊 copy-to-llm 資產、static-i18n 或 MkDocs builder。
- GitHub Actions：PR 只做 build／artifact 檢查，default branch 的 push 才可部署；部署 job 才有 Pages／OIDC 寫入權限，使用 artifact deploy 與鎖定依賴。**啟用 Pages 或首次發布仍需另行同意**。

可重用現有 `scripts/enable-pages.sh` 的框架無關部署邏輯、`references/existing-docs-handling.md` 的內容保護規則，以及 `references/preferences-schema.md:107` 的 namespace 原則；但不新增跨安裝依賴或大型共用抽象。

同步調整舊 `SKILL.md` 的廣泛 trigger，避免兩個 skill 搶接同一請求；在 `skills/.claude-plugin/marketplace.json` 的 `03-infra-and-docs` 登錄新路徑。新 skill 初期是 downstream-only，**不建立 `.agents/skills/`／`.claude/skills/` discovery symlinks**。若新增公開 catalog 頁，遵守英／繁中成對要求。

### 驗證與後續遷移門檻

實作後執行：

```bash
make test-mkdocs-skill
make validate
```

為新 skill 增加獨立測試 target（如 `make test-zensical-skill`）並接到適當 CI；涵蓋第二階段的 build、output assertions、初始化與失敗情境，瀏覽器驗收則確認搜尋／複製等互動。原有 MkDocs 測試保持通過；不修改本 repo 的 `mkdocs.yml` 或現行部署引擎。

建議 **2027 年 1 月再做一次正式盤點**，並在 Material 支援截止前確定各專案的去向；若出現安全問題或原生 i18n 等重要功能則提前重評。這是建議檢查點，本次不建立排程。

舊專案遷移一律逐案要求：**插件與 hooks 盤點 → 舊新站關鍵輸出比對 → 可回復的切換方案 → 使用者同意**。不要因為新 skill 發布而自動遷移既有站點。

## Sources

- [Zensical 0.0.73 release](https://github.com/zensical/zensical/releases/tag/v0.0.73)
- [Zensical 0.0.67：llmstxt 與 Copy as Markdown](https://github.com/zensical/zensical/releases/tag/v0.0.67)
- [Zensical MkDocs plugins 相容性表](https://zensical.org/docs/compatibility/mkdocs/plugins/)
- [Zensical MkDocs 遷移限制](https://zensical.org/docs/compatibility/mkdocs/migration/)
- [Zensical 語言設定](https://zensical.org/docs/setup/language/)／[Roadmap](https://zensical.org/roadmap/)
- [Material 維護公告與 changelog](https://squidfunk.github.io/mkdocs-material/changelog/)
- [Material 對 MkDocs 2.0 的分析（含 2026-10 更新）](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/)
- [Zensical GitHub Pages 部署](https://zensical.org/docs/publish-your-site/)
