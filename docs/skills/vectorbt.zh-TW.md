# vectorbt

協助 agent 將 **VectorBT OSS 或 PRO 當作 Python library** 使用，涵蓋開發、除錯、
效能改善與版本遷移。此 local skill 與
[quantatitive-factor-researcher](quantatitive-factor-researcher.md)
同屬 `quantitative-finance` marketplace group。

Skill 先辨識實際 import、環境與 API。新專案確認有 PRO 存取權時優先推薦 PRO；
現有 OSS 專案則沿用原版，遇到功能缺口、效能需求或明確遷移要求時才評估 PRO。
沒有 PRO 權限仍可使用公開 OSS 文件及已安裝的套件。

## 內容

- 精簡入口與按需讀取的 OSS、PRO、遷移、MCP references。
- `vbt_context.py doctor`：檢查專案 Python、實際 import、套件版本、PRO 存取狀態及快取。
- `vbt_context.py sync-pro`：沿用 GitHub CLI 登入下載 release 資產，驗證 checksum，
  產生保留來源 URL 的 Markdown 與頁面／物件索引；指定 release 時不必安裝 VBT。
- `vbt_mcp.py config`、`serve`、`check`：配置 Codex／Claude Code 專案 MCP、
  啟動官方 PRO server，並驗證真正的 MCP 呼叫。
- 使用合成文件及假的 GitHub CLI 測試；CI 不需要會員權限或私有文件。

原始碼：[local skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/vectorbt)。

## 使用

以下命令相對於已安裝的 skill 目錄；Python 指向你的策略專案。

```bash
python3 scripts/vbt_context.py doctor --project /path/to/strategy
python3 scripts/vbt_context.py sync-pro --python /path/to/strategy/.venv/bin/python
# 只查文件、不安裝 PRO：明確選擇需要的 release
python3 scripts/vbt_context.py sync-pro --release v2026.9.5
```

使用回傳的 `index` 與 `markdown_dir` 進行 `rg` 搜尋，再閱讀完整相關章節並核對
實際 API signature。預設不建立 embeddings，也不需要額外 LLM API key。
預設下載 pages、examples；查 Discord 討論或設定 MCP 時加上 `--messages`。
範例 release 並非固定預設版本。

## XDG 快取與同步

macOS、Linux 使用相同順序：`--cache-dir` → 絕對路徑的
`$XDG_CACHE_HOME/vectorbt-agent` → `~/.cache/vectorbt-agent`。
XDG 未設定、空值或相對路徑皆回退預設值。文件跨專案共用，依 edition／release
隔離；下載檔與憑證不進入 Git。

距上次成功檢查超過 24 小時，或使用 `--refresh` 時，才查遠端 metadata。
資產 ID、更新時間、大小與 digest 能辨識同 tag 的更新；驗證完成後原子切換
有效 generation，正在使用舊文件的程序仍可維持一致內容。不安裝背景排程。

`--offline` 只使用有效本地資料；遠端查詢失敗但仍有有效快取時，明確回報 `stale`。
兩者都不表示內容與即時網站相同。遠端缺少 digest 會標示驗證限制；checksum 或
JSON 錯誤不會取代上一份有效快取。清除舊 generation 前，先停止仍在使用它的程序。

## 可選 MCP

需要時才準備目標版本的官方 MCP／knowledge 依賴、同步三份資產並預覽／套用
專案配置。啟動器使用同一份快取與官方工具，不另外實作檢索引擎。既有同名 server
發生衝突時只做必要合併，不覆寫其他設定。

`check` 會驗證 server 協定、環境、文件讀取及 BM25 搜尋；客戶端仍須載入配置並
成功呼叫工具，才能宣稱完整連線。server 測試成功不等於客戶端已載入。

## 驗證基準

已用 Python 3.12、OSS 1.1.0（Plotly 5.24.1）與 PRO 2026.9.5（MCP SDK 2.2.0）
驗證獨立程序中的人工資料回測、私有資產同步、官方 MCP 頁面／BM25 呼叫，以及
兩個客戶端的隔離 marketplace 載入。這是已測試組合，不是通用的依賴版本限制；
OSS reference 記錄了實際遇到的 Plotly 7 匯入相容性問題。

## 官方來源

- [OSS 文件](https://vectorbt.dev/) 與 [原始碼](https://github.com/polakowo/vectorbt)
- [PRO AI 整合](https://members.vectorbt.pro/using-ai/)、[下載](https://members.vectorbt.pro/downloads/) 與 [Releases](https://github.com/polakowo/vectorbt.pro/releases)
- [XDG 規範](https://specifications.freedesktop.org/basedir/latest/)

撰寫時檢查的官方原始碼尚未附帶 skill；已評估的第三方技能採用不同工作約定，
包含 OpenAlgo 專用的指標預設。因此這份 skill 採自行撰寫。
