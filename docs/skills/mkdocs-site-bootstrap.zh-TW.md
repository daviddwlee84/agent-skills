# mkdocs-site-bootstrap

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

為 repo 啟動一個 MkDocs Material 文件站，並（可選）部署到 GitHub Pages
—— 包含這個 docs 站本身使用的同一個技術組合 (Material + `mkdocs-llmstxt` +
`mkdocs-copy-to-llm` + `pymdownx.snippets`，附 paths-filter 的 GitHub
Pages workflow)。

這個 skill 是 **consent-gated**。它把偏好設定 (preferences) 記錄在
`.skills/preferences.yaml`，避免每次 session 都重問；**永遠不會**自動
遷移使用者既有的 `docs/` 內容；也會在使用者明確同意後才呼叫
`gh api -X POST .../pages`。

## 快速開始

```bash
# 1. Scaffold 站點檔案
bash skills/local/mkdocs-site-bootstrap/scripts/init-docs-site.sh \
  --site-name "My Project" \
  --repo-slug owner/repo \
  --site-url https://owner.github.io/repo/

# 2. 本機驗證
uv sync --extra docs && uv run mkdocs build --strict

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
| `init-docs-site.sh` | Scaffold `mkdocs.yml`、`pyproject.toml`、`docs/`、`.github/workflows/docs.yml` |
| `enable-pages.sh` | 透過 `gh api` 啟用 Pages 並觸發第一次部署 |
| `add-docs-page.sh` | 建立新的 `docs/` 頁面並插入 `mkdocs.yml` nav |
| `check-preferences.sh` | 讀 / 寫 / 重置 `.skills/preferences.yaml` |
| `add-language.sh` | 把非預設語言（例 zh-TW）改裝 (retrofit) 到既有站點 |

所有 script 都支援 `--help` 跟 `--dry-run`。

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
把非英文語言（例如 `zh-TW`）改裝到既有站點 —— 預設保留 `mkdocs-llmstxt`、
並用 `--drop-strict` 自動 patch CI/Makefile：

```bash
bash skills/local/mkdocs-site-bootstrap/scripts/add-language.sh \
  --lang zh-TW --drop-strict
```

完整指引（包含**「中文 (English original)」術語規則**、與 `llmstxt` /
`navigation.instant` 的不相容性）見
[`references/i18n-guide.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-guide.md)。

## 為什麼是 skill 而不是一次性 script？

因為 docs 站不是一次性 setup —— 它會演化。這個 skill 的存在是為了：

1. 把最初的 scaffold 做對 (consent-gated、idempotent)。
2. 之後持續用 `add-docs-page.sh` 幫忙加頁面。
3. 記住使用者已經做過的決定，未來 session 不要煩人。
4. 提供一個地方編碼那些 gotcha (連結規則、snippets dir、`pages: write`
   權限等)，避免每個 project 都要重新發現。

附帶的 `references/docs-stack-recipe.md` 文件化技術組合實際上是什麼，
這樣想手動套用零件的使用者不必調用 skill 也能拿到配方。

## Canonical SKILL.md

完整觸發描述、工作流程、與 gotcha 見
[skills/local/mkdocs-site-bootstrap/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/SKILL.md)。
