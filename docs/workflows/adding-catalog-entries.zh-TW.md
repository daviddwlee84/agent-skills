# Adding catalog entries —— 加入 catalog 條目

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

如何新增或更新 [Catalog](../catalog/index.md) 條目 —— 新的 external
skill、新的 MCP server、新的 domain hub，或既有條目的 status 變更。

此 workflow 把 catalog 與既有的 source of truth（`vendor.yaml` 與
`TODO.md`）耦合而不重複。Catalog 頁面是*vendoring 決策紀錄*；實際的
vendoring 透過既有 script 進行。

## 何時寫一筆 catalog 條目

| 你發現了… | 放哪 | 起始 status |
|---|---|---|
| 可能想 vendor 的 external skill | [`skill-collections.md`](../catalog/skill-collections.md) + 對應的 [domain hub](../catalog/domains/index.md) | `wishlist` |
| 明確不想進日常 discovery，但值得收藏的有趣 skill | [`curiosities.md`](../catalog/curiosities.md) | `skipped`，並寫明只放 docs 的理由 |
| 想記住的 MCP server | [`catalog/mcp/`](../catalog/mcp/index.md) 下新檔 + 對應的 domain hub | `wishlist` |
| 全新的專業領域 (professional domain) | [`catalog/domains/`](../catalog/domains/index.md) 下新檔（複製 `_template.md`） | （hub 本身，不是條目） |
| 看過後決定不要 vendor 的 skill | 加進 `skill-collections.md` 並寫理由 | `skipped` |
| 看過但還沒決策的 skill | 加進 `skill-collections.md` 寫一句話備註 | `evaluated` |

## Status enum

--8<-- "_snippets/external-install.md"

## Status 變更 recipe

### `wishlist` → `deferred`

條目跨入「該評估這個」的階段。

```bash
./scripts/add-todo.sh --priority P? --effort <S|M|L> \
  --title "<skill-name> skill" \
  --description "Evaluate <upstream URL> for <use case>. See catalog/<page>.md."
```

然後編輯 catalog 條目：把 `status: wishlist` → `status: deferred`，
連結到新建的 TODO 行。

### `deferred` → `vendored`

條目已評估完，決定 vendor。

```bash
# Vendor 該 skill（寫進 vendor.yaml + 下載檔案）
./scripts/add-vendor.sh <owner>/<repo>/<path-to-skill>

# 或加 series 子目錄
./scripts/add-vendor.sh --series <series-name> <owner>/<repo>/<path-to-skill>

# 若該條目有 TODO P? 行，promote 它
./scripts/promote-todo.sh --title "<substring>" \
  --summary "Vendored from <upstream URL>"
```

然後編輯 catalog 條目：把 `status: deferred` → `status: vendored`，
更新連結指向 `skills/vendor/<name>/`（或
`skills/vendor/<series>/<name>/`）。

### `wishlist` / `evaluated` → `skipped`

讀完 upstream 後決定不 vendor。

直接編輯 catalog 條目：status → `skipped`，inline 寫一句話理由。範例：

- 「Skipped —— 與 `<other-skill>`（來自更權威的 `<source>`）重複。」
- 「Skipped —— Slack 專屬；不通用。」
- 「Skipped —— 比既有的 `<existing-local-skill>` 更窄且重疊。」

## 加一筆新的 MCP 條目

1. 建立 `docs/catalog/mcp/<slug>.md`，附上
   [`mcp/index.md`](../catalog/mcp/index.md#per-entry-conventions)
   文件化的 YAML frontmatter schema。
2. 填上六段式 (6-section) 主體（TL;DR / capabilities / install /
   when / related / sources）。
3. 翻譯成 `docs/catalog/mcp/<slug>.zh-TW.md`。
4. 把它加到 `mkdocs.yml` 的 nav 之 `Catalog → MCP wiki` 下方。
5. 在 [`mcp/index.md`](../catalog/mcp/index.md) 的 entries table 加一列。
6. 從相關 domain hub 的 MCP 段落交叉連結 (cross-link)。

當 MCP wiki 條目 ≥ 5，索引表將由 script 重建（規劃中 —— 見後續 TODO）。
在那之前手動編輯該表。

## 加一個新的 domain hub

見 Domains 總覽中的
[How to add a new domain hub](../catalog/domains/index.md#how-to-add-a-new-domain-hub)
段落 —— recipe 與 template 放在一起。

## 雙語 (bilingual) 義務

`docs/catalog/` 內的每個頁面（除了 snippet 與 `_template.md`）都必須
有 `*.zh-TW.md` 對應檔。`mkdocs-i18n` 的 `fallback_to_default: true`
讓缺翻譯不會弄壞 build，但專案慣例是每個發布頁面在同一個 PR 內
就有兩種語言。

## 驗證

```bash
make docs-build       # strict mode 抓缺 snippet / 壞掉的 link
make marketplace      # 確保 vendor.yaml / marketplace.json 沒退步
make kanban           # 確保 TODO.md 仍然 parse 得過
```

打開 served site（`make docs-serve`），點過新條目的交叉連結
驗證它們可達。
