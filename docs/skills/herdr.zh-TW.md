# herdr（vendored）

從官方
[`herdrdev/herdr/skills/herdr`](https://github.com/herdrdev/herdr/tree/master/skills/herdr)
skill vendor 而來，採 Apache-2.0 授權。它透過 `vendor.yaml` 同步；不要在本機
編輯 vendored 檔案，因為 `make sync` 會覆寫它們。

## 教什麼

這個 skill 提供 agent 操作 Herdr session、workspace、tab、pane 與已識別
agent API 的安全模型。它強調明確 ID、JSON response、`--current`、不搶焦點的
背景 pane、依生命週期等待，以及 raw pane control 與 agent control 的差異。

它只會在使用者明確要求使用 Herdr 時觸發，且控制 live session 前要求
`HERDR_ENV=1`。

## 版本對齊

這份 vendored copy 適合 catalog discovery 與一般安裝。同一台機器若也安裝
Herdr binary，應優先使用該 binary 輸出的精確 skill：

```bash
herdr --skill > ~/.agents/skills/herdr/SKILL.md
```

如此 CLI syntax 與 skill 指引會維持在同一 release，包含 preview build。
配套 dotfiles 已自動實作這個流程。

## Canonical SKILL.md

完整指示見
[`skills/vendor/herdr/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/herdr/SKILL.md)。
