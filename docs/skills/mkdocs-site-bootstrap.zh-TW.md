# mkdocs-site-bootstrap

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

為 repo 啟動一個 MkDocs Material 文件站，並（可選）部署到 GitHub Pages
—— 包含這個 docs 站本身使用的同一個技術組合 (Material + `mkdocs-llmstxt` +
`mkdocs-copy-to-llm` + `pymdownx.snippets`，附 paths-filter 的 GitHub
Pages workflow)。多語站採用 strict two-pass build，讓 root llms 檔保持完整，
而且只包含預設語言。

這個 skill 是 **consent-gated**。它把偏好設定 (preferences) 記錄在
`.skills/preferences.yaml`，避免每次 session 都重問；**永遠不會**自動
遷移使用者既有的 `docs/` 內容；也會在使用者明確同意後才呼叫
`gh api -X POST .../pages`。

!!! warning "已在使用舊版 skill？"
    更新已安裝的 skill 只會下載修正後的 build 與 migration 工具，**不會**
    修改你的 project。如果加 i18n 後 `llms.txt` 幾乎為空、變成最後一個
    locale，或 CI 曾被迫拿掉 strict，請依下方的
    [遷移既有站點](#migrate-existing-site) 操作。

## 快速開始

```bash
# 1. Scaffold 站點檔案
bash skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/

# 2. 建立完整 strict artifact（HTML + 預設語言 llms）
uv sync --extra docs
uv run python scripts/build-docs-site.py

# 3. 啟用 GitHub Pages 並觸發第一次部署 (consent gate)
bash skills/local/mkdocs-site-bootstrap/scripts/enable-pages.sh \
  --repo owner/repo

# 4. 之後新增頁面
bash skills/local/mkdocs-site-bootstrap/scripts/add-docs-page.sh \
  --section Reference --title "API schema"
```

## 附帶的 script

| Script | 用途 |
|---|---|
| `init-docs-site.sh` | Scaffold config、docs、workflow、與 managed production build helper |
| `build-docs-site.py` | Strict production build；隔離多語 HTML 與預設語言 llms 輸出 |
| `enable-pages.sh` | 透過 `gh api` 啟用 Pages 並觸發第一次部署 |
| `add-docs-page.sh` | 建立新的 `docs/` 頁面並插入 `mkdocs.yml` nav |
| `check-preferences.sh` | 讀 / 寫 / 重置 `.skills/preferences.yaml` |
| `add-language.sh` | 把非預設語言（例 zh-TW）改裝 (retrofit) 到既有站點 |
| `migrate-i18n-llmstxt.sh` | Audit 或保守遷移舊版 i18n + llmstxt scaffold |

所有 script 都支援 `--help` 跟 `--dry-run`。

## Production build 與 preview

要部署的 artifact 一律用：

```bash
uv run python scripts/build-docs-site.py
```

保留 llmstxt 的多語站中，helper 先跑 strict 的預設語言 llmstxt pass，再跑
獨立的 strict 多語 HTML pass；驗證後才合併 root artifact 並替換 `site/`。
`/llms.txt`、`/llms-full.txt`、以及 raw `.md` sidecar 刻意只代表預設語言。

直接執行 `uv run mkdocs build --strict` 或 `uv run mkdocs serve` 是安全的
HTML-only preview，因為 scaffold 預設停用 llmstxt，只有 helper 會在隔離的
pass 中啟用它。若站點承諾提供 llms 輸出，不要部署直接多語 build 的結果。

## 偏好設定 (Preferences)

skill 寫入 `<repo>/.skills/preferences.yaml`：

```yaml
mkdocs_site_bootstrap:
  enabled: true
  decided_at: "2026-04-23"
  stack: mkdocs-material
  auto_deploy: true
  pages_deployed: true
  existing_docs_decision: skipped
  site_url: https://owner.github.io/repo/
  repo_slug: owner/repo
  # i18n keys
  languages: ["en", "zh-TW"]
  keep_english_terms: true
  i18n_structure: suffix
```

要改變主意：

```bash
# 重置 (回到「從未詢問」狀態)
bash skills/local/mkdocs-site-bootstrap/scripts/check-preferences.sh \
  --reset mkdocs_site_bootstrap

# 或顯式 opt out 讓 agent 停止詢問
bash skills/local/mkdocs-site-bootstrap/scripts/check-preferences.sh \
  --set mkdocs_site_bootstrap.enabled=false
```

完整 schema 與跨 skill 偏好慣例見
[`references/preferences-schema.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/preferences-schema.md)。

## 既有的 `docs/` 內容

這個 skill 會偵測到既有 `docs/` 內容、並在做任何事之前**先問**。
它**永遠不會**自動遷移、改名、改寫使用者的檔案。三個 consent 選項：

- **skip** —— 不動 docs，只建立 `mkdocs.yml` 配空白 nav (auto-generate)
- **wrap** —— 同 skip，但用既有檔案依字母順序填入 `nav:`
- **manual** —— 中止，使用者先重組再重跑

完整決策樹見
[`references/existing-docs-handling.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/existing-docs-handling.md)。

## 雙語 / 多語 docs

這個 skill 也支援透過
[`mkdocs-static-i18n`](https://github.com/squidfunk/mkdocs-material/discussions/2346)
把非英文語言（例如 `zh-TW`）改裝到既有站點，同時保留 strict 與預設語言
`mkdocs-llmstxt`：

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh \
  --lang zh-TW
uv sync --extra docs
uv run python scripts/build-docs-site.py
```

完整指引（包含**「中文 (English original)」術語規則**、與 `llmstxt` /
`navigation.instant` 的互動、plugin guard、與 two-pass build）見
[`references/i18n-guide.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-guide.md)。

`--remove-llmstxt` 是顯式 opt-out。舊的 `--drop-strict` 現在是 deprecated
no-op，因為拿掉 strict 只會隱藏 warning，不會修好被覆寫的輸出；
`--keep-llmstxt` 是現行預設行為的 deprecated alias。
Exit `11` 表示語言已加入，但自訂的下游 build 檔仍需完成 migration 工具
回報的 manual action。

## 遷移既有站點 {#migrate-existing-site}

在下游 project root 先更新工具，再執行 audit：

```bash
npx skills@latest update mkdocs-site-bootstrap --project --yes

bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --json
```

Exit `10` 表示找到受影響的 legacy 形狀，而且尚未改任何檔案。先預覽，再
apply 並驗證：

```bash
bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --dry-run --json

bash .agents/skills/mkdocs-site-bootstrap/scripts/migrate-i18n-llmstxt.sh \
  --target-dir . --apply --verify --json
```

工具只 patch 可辨識、由 scaffold 擁有的 config、workflow、Makefile 與
managed helper 形狀。自訂值或同名但非 managed 的 helper 會列在
`manual_actions[]` 並保持不動；exit `11` 讓人工工作維持可見。它也會回報
localized source 裡不安全的相對 llms／sidecar link，讓使用者手動換成包含
project subpath 的完整 `site_url` URL。完整契約見
[`migration guide`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-llmstxt-migration.md)。

## 為什麼是 skill 而不是一次性 script？

因為 docs 站不是一次性 setup —— 它會演化。這個 skill 的存在是為了：

1. 把最初的 scaffold 做對 (consent-gated、idempotent)。
2. 之後持續用 `add-docs-page.sh` 幫忙加頁面。
3. 記住使用者已經做過的決定，未來 session 不要煩人。
4. 提供一個地方編碼那些 gotcha (連結規則、snippets dir、`pages: write`
   權限、i18n/llmstxt lifecycle 隔離等)，避免每個 project 都要重新發現。

附帶的 `references/docs-stack-recipe.md` 文件化技術組合實際上是什麼，
這樣想手動套用零件的使用者不必調用 skill 也能拿到配方。

## Canonical SKILL.md

完整觸發描述、工作流程、與 gotcha 見
[skills/local/mkdocs-site-bootstrap/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/SKILL.md)。
