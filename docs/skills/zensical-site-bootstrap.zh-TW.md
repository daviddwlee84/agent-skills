# zensical-site-bootstrap

英文限定的 Zensical 文件試點：安全初始化、鎖定 uv 文件依賴、原生 LLM 匯出，以及只建置不部署的 CI。

[Skill 原始碼與工具](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/zensical-site-bootstrap)

## 提供的能力

- 明確指定目標、支援 dry-run，拒絕覆寫既有文件站設定。
- 可保留經確認的 `docs/`，不自動重組內容。
- Zensical 0.0.73 放在 docs 依賴群組，不加入應用程式 runtime dependencies。
- 原生 `llms.txt`、`llms-full.txt`、Markdown 匯出與 Copy as Markdown。
- Mermaid 流程圖與可指定 host／port 的預覽指令。
- 專案自有的檢查腳本，驗證內容完整性、複製目標與 Pages 子路徑。
- 可選 GitHub Actions 建置檢查，不包含部署權限。

第一個實際試用（dogfood）專案是 [ferry](https://github.com/daviddwlee84/ferry)。
產生的檔案屬於使用端專案，不依賴本 skills repo 的本地 checkout。

## 範圍限制

這不是 MkDocs 遷移工具，也沒有實作內容多語的缺譯回退（fallback）。
若需要英文為主、部分繁中且缺譯時回退英文，先使用
[mkdocs-site-bootstrap](mkdocs-site-bootstrap.md)，直到 Zensical 的對應能力通過驗證。
語言選單不等於內容多語。發布 GitHub Pages 仍需另外同意。

## 安裝

Skill 發布到目錄後：

```bash
npx skills@latest add daviddwlee84/agent-skills/skills --skill zensical-site-bootstrap
```

安裝或更新 skill 不會覆寫使用端的文件、設定、檢查腳本與 workflow。
採用新版範本或建置工具時，應明確檢視專案檔案差異。
