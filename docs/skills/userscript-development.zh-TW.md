# userscript-development

專門開發與除錯 userscript，明確區分執行環境與測試證據。
這個 owned skill 由 [Tampermonkey-Scripts](https://github.com/daviddwlee84/Tampermonkey-Scripts)
維護 canonical；本 collection 在 `skills/owned/userscript-development/` 分發同步副本。
更新方式見 [owned 工作流程](../workflows/adding-owned-skills.md)。

## 整理了哪些經驗

| 實際經驗 | Skill 的做法 |
|---|---|
| 換頁後按鈕消失 | 冪等 (idempotent) reconciliation、目標替換、路由狀態失效 |
| 標題一直重複加前綴 | Observer callback 是非同步的；寫入前比對期望狀態 |
| Console 成功，manager 失敗 | 分別檢查 grant、sandbox、URL match、注入權限與時機 |
| 匯出混入自己的面板或譯文 | 複製後清理、排除自有 UI、保留來源快照 (snapshot) |
| UI 截圖沒問題，實際內容卻錯 | 檢查剪貼簿、下載檔與部分匯出報告 |
| 腳本與網站／原生擴充快捷鍵衝突 | 用實際鍵盤輸入測 Shadow DOM event path、IME 與焦點歸屬 |
| Chromium／Firefox fixture 通過 | 將 DOM／shim 證據與真實 manager 證據分開 |
| 與原生參考資料一致 | 靜態模型核對不等於真的載入 reference extension |

主 skill 為 146 行，附六份 reference、三檔可執行測試範例與輸出忽略設定。
來源對照與修正過的假設記在
[provenance reference](https://github.com/daviddwlee84/Tampermonkey-Scripts/blob/main/.agents/skills/userscript-development/references/provenance.md)。

資源相對於實際載入的 skill 安裝目錄定位；專案命令、依賴與測試輸出都放在使用者的
工作專案，不需要作者的 checkout。來源專用命令留在該專案的 CLAUDE.md，公開來源
連結僅供查核經驗出處。

## 瀏覽器與 extension 測試

包含用專案鎖定版本的 Playwright 安裝瀏覽器、撰寫本機 HTML fixture、
按確定順序注入 GM shim、用 Chromium／Firefox 互動，以及保存截圖和實際輸出。
2026-09-09 使用 `skills@1.5.25 add --copy` 真正安裝到含空格路徑的乾淨專案，
再於該專案獨立安裝 Playwright 1.62.1，直接執行安裝版 reference 的複製與測試步驟。
兩個引擎共 **6/6 測試通過**，截圖已目視檢查，11 個安裝的 skill 檔案均未被改寫。

真實 manager 部分涵蓋 bundled Chromium 的 persistent context、隔離 profile、
官方 extension 安裝包、實際 ID 探索、權限開關，以及透過 manager UI 匯入 `.user.js`。
Reference 測試則在同一個 fixture 比較「原生擴充單獨」、「userscript 單獨」與「兩者共存」。

這套程序來自來源專案的
[VM／TM ＋ Vimium C 實測紀錄](https://github.com/daviddwlee84/Tampermonkey-Scripts/blob/d7525d2/userscripts/vimium-c-companion/VALIDATION.md)
及實際檢視過的本機實驗。這些歷史結果在撰寫 skill 時是查核紀錄，沒有重新執行。
Firefox DOM 測試可用，但來源專案的真實 Firefox manager 嘗試尚未證明 userscript 注入成功。

## 查過的現有 skill

先檢查 skills.sh leaderboard，再用 `skills@1.5.25 find userscript` 與
`find tampermonkey` 搜尋，接著檢視 upstream。數字是 2026-09-09 的快照，不代表正確性保證。

| 候選 | 查核結果 | 決策 |
|---|---|---|
| [henkisdabro tampermonkey](https://skills.sh/henkisdabro/wookstar-claude-plugins/tampermonkey) | 225 次安裝；GitHub repo 86 stars；檢視 `5091ecc` 的 SKILL.md 與 patterns | `skipped`：可作 TM API 參考，但本專案需要精簡的跨 manager lifecycle 與 fixture／native 測試工作流，因此不 vendor |
| [xixu-me develop-userscripts](https://skills.sh/xixu-me/skills/develop-userscripts) | 12 次安裝；目錄描述涵蓋 Tampermonkey／ScriptCat；GitHub API 回傳 404 | `evaluated` 僅限 listing；canonical、stars 與可安裝性尚未確認 |
| [andradeatdev userscript-creator](https://skills.sh/andradeatdev/skills/userscript-creator) | 1 次安裝；GitHub API 回傳 404 | `wishlist`；未讀到內容，目前不推薦安裝 |

第一個候選的已查核原始碼在
[此處](https://github.com/henkisdabro/wookstar-claude-plugins/blob/5091eccfb7cf09275f20fda850c190dff83be100/plugins/tampermonkey/skills/tampermonkey/SKILL.md)。
手動安裝命令為
`npx skills@1.5.25 add henkisdabro/wookstar-claude-plugins --skill tampermonkey`。
本次沒有安裝外部 skill，也沒有把外部 skill 內容複製進 collection。

新 skill 採原創文字，依據自己的專案經驗整理。價值是特定失敗模式與可重複的驗證程序，
不是一般 JavaScript 教學。尚未做有／無 skill 的受控模型比較；
輸出品質與觸發率可另交由 `skill-creator` 評估。

## 安裝與維護

Canonical 位於來源專案的 `.agents/skills/userscript-development/`。
來源已發布，owned 條目透過 `vendor.yaml` 記錄 upstream commit。
現在可直接從已發布來源安裝：

```bash
npx skills@1.5.25 add daviddwlee84/Tampermonkey-Scripts --skill userscript-development
```

此 collection 的更新副本發布後，也可透過分組 picker 安裝：

```bash
npx skills@1.5.25 add daviddwlee84/agent-skills/skills --skill userscript-development
```

本機開發時，可從本機 checkout 安裝，或使用來源專案的 discovery 目錄。
後續請修改來源專案，不在 owned 副本各自維護。
