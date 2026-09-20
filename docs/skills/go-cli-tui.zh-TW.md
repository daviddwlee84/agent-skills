# go-cli-tui

開發 Go 命令列工具 (CLI)、終端使用者介面 (TUI) 與互動設定 wizard，
以 Lazygit 的操作體驗為基準：看得見狀態、快速切換情境、容易找到動作，
操作後立即得到回饋。預設採 Cobra，加上版本相容的 Bubble Tea、Bubbles、
Lip Gloss，表單需要時使用 Huh。

這是可獨立安裝的 local 開發 skill，包含主文件與五份參考文件，不附 starter
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

收到實作要求時，skill 會從精簡互動規格、共用領域操作一路做到實作與驗證，
不會停在畫面建議。

## 互動預設

| 面向 | 行為 |
|---|---|
| 導航 | 方向鍵與 j/k 並存；Tab/Shift+Tab 切焦點；依情境提供 h/l；長列表支援 gg/G |
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
執行前呈現實際目標與變更摘要。

## 包含的參考文件

| 文件 | 適用情境 |
|---|---|
| [互動設計](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/interaction-design.md) | 畫面、焦點、雙導航、篩選、help、Unicode 與 resize |
| [CLI、wizard、config](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/cli-wizards-config.md) | 入口規則、表單、共用驗證、XDG 與優先序 |
| [Charm 工具選用](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/charm-stack.md) | 版本辨識、依需求選擇函式庫或工具 |
| [非同步與終端](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/async-terminal.md) | 請求世代、取消、啟動、終端控制權與 dev-cli 經驗 |
| [驗證](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/references/verification.md) | 狀態測試、真實 PTY 操作與三種驗收案例 |

Charm 速查包含 Glamour、Log、Wish、ANSI／terminal utilities、Harmonica、
Gum、Glow、VHS 與 Freeze 等可選能力，不會把所有工具都加入依賴。
新程式先確認相容的穩定版本；既有程式先讀 module 版本再參考範例。

## 來源與限制

[Lazygit](https://github.com/jesseduffield/lazygit/blob/master/AGENTS.md) 使用
自行維護的 gocui fork。本 skill 參考它的 UX，新專案實作則偏好
[Charm](https://charm.land/)。也抽取 [dev-cli](https://github.com/daviddwlee84/dev-cli)
的 live filter、請求世代處理、共用 wizard 與終端交接經驗，不依賴該專案，
也不複製它的領域模型。

[外部 catalog](../catalog/skill-collections.md#go-clitui-candidates) 記錄
2026-09-20 對 `golang-cli`、`tui-design` 與 `bubbletea` 的比較、手動安裝方式，
以及本 repo 選擇自製整合的理由。

驗證指引包含確定性的狀態測試、錯誤參數／JSON／設定檢查，以及實際終端操作。
三種 walkthrough 是驗收規格，不是已執行的 app 或 skill benchmark。
發佈需求可搭配可選的 [CLI release skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/cli-release-distribution)。

## Canonical SKILL.md

完整指令見 [skills/local/go-cli-tui/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/go-cli-tui/SKILL.md)。
