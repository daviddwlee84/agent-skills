# go-cli-tui

開發 Go 命令列工具 (CLI)、終端使用者介面 (TUI) 與互動設定 wizard，
以 Lazygit 的操作體驗為基準：看得見狀態、快速切換情境、容易找到動作，
操作後立即得到回饋。預設採 Cobra，加上版本相容的 Bubble Tea、Bubbles、
Lip Gloss，表單需要時使用 Huh。

這是可獨立安裝的 local 開發 skill，包含主文件與十份參考文件，不附 starter
專案。主要服務從零開發與新增功能，也保留既有專案的框架與公開操作契約。

## 安裝與使用

```bash
npx skills@latest add daviddwlee84/agent-skills/skills --skill go-cli-tui
```

分組選單列在 **go-cli**。可以這樣要求 agent：

- 「用 Go 做一個資源管理工具，要有 Lazygit 風格的列表與預覽、方向鍵／Vim
  導航，以及背景 refresh。」
- 「加入 `hosts add` wizard，讓使用者不用記住所有 flags 也能完成設定。」
- 「改善這個 Bubble Tea v1 app 的焦點、搜尋與刷新體驗，保留原本框架版本。」
- 「讓 agent 能可靠使用這個 CLI，提供內建操作指南與機器輸出，再準備第一個
  `go install` 版本。」
- 「加入 upgrade 命令，更新目前執行的那份 binary，並依原始碼建置、release
  assets 或套件管理器擁有權選擇正確流程。」

收到實作要求時，skill 會從精簡互動規格、共用領域操作一路做到實作與驗證，
不會停在畫面建議。

## 互動預設

| 面向 | 行為 |
|---|---|
| 導航 | 方向鍵與 j/k 並存；Tab/Shift+Tab 切焦點；依情境提供 h/l；長列表支援 gg/G |
| 滑鼠 | 共用純 layout／hit geometry、語意化按下／放開動作、modal 捕捉，以及可關閉以恢復原生選字 |
| 文字輸入 | 可列印按鍵維持文字輸入，不要求先學 normal／insert mode |
| 操作提示 | 情境 footer、help 與 action menu 使用同一份有效按鍵定義 |
| 狀態延續 | 切換、refresh 與 wizard 返回時保留有效選取、篩選與捲動位置 |
| 回應速度 | 慢速工作前先顯示畫面；丟棄過期結果；區分快取、未知、空結果與失敗 |
| 偏好設定 | 可選 TOML；macOS/Linux 採 XDG，Windows 採原生路徑；flags → env → file → defaults |

有 dashboard 的 app 在 TTY 裸啟動時開啟介面。指定支援 wizard 的命令，例如
`hosts add`，裸呼叫時進入引導；一般命令群組顯示 help。已帶部分業務 flags
卻缺必要資料時回報用法錯誤；明確指定 `--interactive` 才進入預填的 wizard。
只有 `--config` 等全域選項時，仍視為裸的 wizard 入口。

未知 flag 或不合法的值會在互動前回報。非 TTY 與 JSON 模式不發問；互動與
輸出模式互相衝突時明確報錯。Wizard 的 Back 保留答案，與 CLI 共用驗證，
有重要影響的套用前呈現實際目標與變更摘要。預填的本機設定表單可從任何欄位
按 Ctrl+S 儲存，保留可選的 Review、共用驗證與失敗時的草稿；在真實 PTY
驗證原始 Ctrl+S 按鍵與終端 flow control。

## Agent 使用與分階段安裝

當工具需要支援 agent 操作時，skill 包含將唯一的操作指南嵌入 binary、離線
可讀的 `--skill`／主題輸出、JSON 錯誤、非互動認證行為與有界限的日誌串流。
CLI、TUI 與 agent 呼叫使用相同的領域操作。命令 help 是語法的依據；指南
說明流程、作用範圍與結果不確定的寫入。不要求所有工具都附帶 skill 或安裝器。

Go 工具的初期發佈可從 `go install` 開始，使用實際 main package 路徑；
若 repo 採用 `cmd/<name>` 結構，安裝路徑也要包含它。文件交代 Go 版本需求
與 binary 的 `PATH`，缺少 linker flags 時從安裝模組取得版本，並在 checkout
外驗證公開的固定 tag 與 `@latest`。`@latest` 通常不代表最新的 main commit。
等發佈需求增加，再加入預編譯壓縮檔、checksums 與 Homebrew tap；這些不是
第一個原始碼發佈版本的必要條件。

明確要求升級功能時，依已發佈的產物與目前 executable 的擁有權選擇策略。
只有原始碼的 release 可使用已安裝的 Go 建置確切 tag；預編譯壓縮檔要驗證
checksum 與 executable；套件管理器擁有的版本由該管理器更新。Build metadata
說明建置來源，不代表由誰安裝。搬移過的 Go binary 應更新目前解析後的路徑，
不受現在的 `GOBIN` 或 `PATH` 上另一份副本影響。預設保留本機／dirty build；
暫存建置、目標鎖定、檔案身分重查與原子替換，讓失敗時舊檔仍可使用。
Check-only／JSON／read-only 與 Go toolchain 選擇策略要明確；缺少 Go 命令時，
updater 不會自行下載安裝它或執行 `sudo`。內建 `--skill` 內容隨 binary 更新，
使用者不必為此執行 `npx skills`。

滑鼠驗證結合狀態測試與真實 PTY 的 SGR 事件，包含 modal 捕捉，以及縮放或
切換 target 後取消舊按鈕按壓。監控畫面的指引涵蓋帶時間戳的有界歷史、各資料源
的新鮮度、真實斷線缺口、計數器重設與精確 drilldown。設定檔損壞時仍應能開啟
editor，並保留未通過驗證的使用者修改。

維護面向使用者的 changelog，對實際要發佈的程式碼完成檢查，並讓 changelog
版本、不可覆寫的 tag、release notes 與安裝後 binary 版本一致。這些是完成發佈
的檢查項目，不表示每次都要加入套件管理或預編譯打包。

## Completion 與共用操作經驗

Completion 分成生成、安裝使用者檔案、啟用父 shell 與離線候選查詢。
原生 zsh bridge 可以查詢目前 binary，舊式 Bash 輸出則可能需要重新生成。
使用隔離 shell 實測 Tab 輸入，不能只驗證生成檔的語法。

跨 target 與持久化 owner 流程由 CLI/TUI 共用預覽及套用服務。Digest 能偵測
過期狀態，無法把多次遠端寫入變成原子交易。分開記錄來源保存、owner 啟用和
實際 runtime 行為；背景 discovery 不應取代進行中的操作畫面。操作完成後
保留舊資料並標記 stale，再更新受影響的快取。

SSH 認證透過明確動作把終端交給原生 SSH；背景檢查不發問。使用者設定的
共用 master 與 app 自有的備用 session，分別管理生命週期及清理責任。

獨立 shell 整合使用固定格式的環境交接，保留原值、functions 與 exit hooks，
認證不混入被擷取的輸出。持久化 shell 連線明確記錄擁有權及異常退出清理；
產生容器設定時辨識真正的 consumer，保留既有設定管理器的責任。反向 SSH
分清命令、shell 與服務的生命週期，驗證遠端實際監聽位址，將分配埠號的 stdout
與診斷分開，保留 login rc 的優先序並提供明確的 clean-shell 選項。Dashboard
可釋放終端給同一套 CLI wizard，保留結果直到使用者確認，再刷新正確 target。
空搜尋與被裁掉的 Apply 按鈕都不能提交隱藏的選項。

## 包含的參考文件

| 文件 | 適用情境 |
|---|---|
| [互動設計](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/interaction-design.md) | 畫面、焦點、雙導航、篩選、help、Unicode 與 resize |
| [CLI、wizard、config](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/cli-wizards-config.md) | 入口規則、表單、共用驗證、XDG 與優先序 |
| [Charm 工具選用](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/charm-stack.md) | 版本辨識、依需求選擇函式庫或工具 |
| [非同步與終端](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/async-terminal.md) | 請求世代、取消、啟動、終端控制權與 dev-cli 經驗 |
| [Agent CLI](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/agent-facing-cli.md) | 內建知識、靜態文件、機器錯誤、非互動呼叫與有界串流 |
| [Go 發佈](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/go-distribution.md) | Main package 安裝路徑、版本回報、公開 tags 與後續打包 |
| [自我更新](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/self-update.md) | 依條件選擇原始碼／產物／管理器策略、建置來源與擁有權、更新目前副本，以及失敗時保留舊版 |
| [Shell completion](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/shell-completion.md) | Install/status、zsh fpath、離線候選、更新行為與真實 Tab 驗證 |
| [Shell context](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/shell-context.md) | 父 shell 環境、持久化連線、舊 helper adapter 與 consumer 設定擁有權 |
| [驗證](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/verification.md) | 狀態測試、真實 PTY 操作、Unicode emulator 限制與三種驗收案例 |

Charm 速查包含 Glamour、Log、Wish、ANSI／terminal utilities、Harmonica、
Gum、Glow、VHS 與 Freeze 等可選能力，不會把所有工具都加入依賴。
新程式先確認相容的穩定版本；既有程式先讀 module 版本再參考範例。

## 來源與限制

[Lazygit](https://github.com/jesseduffield/lazygit/blob/master/AGENTS.md) 使用
自行維護的 gocui fork。本 skill 參考它的 UX，新專案實作則偏好
[Charm](https://charm.land/)。也抽取 [dev-cli](https://github.com/daviddwlee84/dev-cli)
的 live filter、請求世代處理、共用 wizard、終端交接、內建 skills 與版本回報
經驗，不依賴該專案，也不複製它的領域模型。

[外部 catalog](../catalog/skill-collections.md#go-clitui-candidates) 記錄
2026-09-20 對 `golang-cli`、`tui-design` 與 `bubbletea` 的比較、手動安裝方式，
以及本 repo 選擇自製整合的理由。

驗證指引包含確定性的狀態測試、錯誤參數／JSON／設定檢查，以及實際終端操作。
lazyclash 的具體案例記錄 pyte 0.8.2 的 VS16／ZWJ 重播限制，以及為何需要
直接 View 檢查搭配 PTY 輸入測試。三種 walkthrough 仍是驗收規格，
不是已執行的 app 或 skill benchmark。
發佈需求可搭配可選的 [CLI release skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/cli-release-distribution)。

## Canonical SKILL.md

完整指令見 [skills/local/go-cli-tui/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/SKILL.md)。
