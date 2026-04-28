# How `npx skills` reads catalog metadata — `npx skills` 怎麼讀 catalog metadata

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這頁記錄 `npx skills@latest add ...` 分組安裝 UI 背後的已驗證機制。
以下內容全部由實際閱讀 npm package 原始碼（`vercel-labs/skills`，
[`src/plugin-manifest.ts`](https://github.com/vercel-labs/skills/blob/main/src/plugin-manifest.ts)
和 [`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts)）
以及官方
[Claude Code plugin-marketplaces 文件](https://code.claude.com/docs/en/plugin-marketplaces)
確認。

## 給這個 repo 的 TL;DR

- 你跑 `npx skills@latest add daviddwlee84/agent-skills/skills` 時看到的
  分組 picker UI 是由 `skills/.claude-plugin/marketplace.json` 驅動的 ——
  **在** `skills/` 目錄**裡面**，不是 repo 根目錄。
- 每個分組標頭 (group header) 是 `kebabToTitle(plugins[].name)`。
  沒被列在任何 plugin 底下的 skill 會 fall through 到 **Other** 分組。
- 用手編輯 manifest；跑 `make marketplace`（= `bash
  scripts/validate-marketplace.sh`）抓出壞掉的路徑、重複條目、
  或會被靜默歸到 "Other" 的 on-disk skill。
- 我們**不**出貨 `.claude-plugin/plugin.json` —— 那只是給單一 plugin
  repo 用的。

## CLI 怎麼解析 manifest 路徑

使用者給 `npx skills add` 的引數會被解析成 `repo` + 可選的 `subpath`。
以這個 repo 為例：

```
npx skills@latest add daviddwlee84/agent-skills/skills
                       └────────── repo ──────────┘ └sub┘
```

CLI 內部
([`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts))：

```ts
const searchPath = subpath ? join(basePath, subpath) : basePath;
// ...
const pluginGroupings = await getPluginGroupings(searchPath);
```

所以當安裝指令**包含** subpath 時，CLI 會從
`<repo>/<subpath>/.claude-plugin/marketplace.json` 讀 catalog。

| 調用 | CLI 找 manifest 的位置 |
|---|---|
| `npx skills add anthropics/skills` | `<repo>/.claude-plugin/marketplace.json` |
| `npx skills add daviddwlee84/agent-skills/skills` | `<repo>/skills/.claude-plugin/marketplace.json` |
| `npx skills add foo/bar/some/dir` | `<repo>/some/dir/.claude-plugin/marketplace.json` |

這個 repo 用第二種形式，因為 `skills/local/` 跟 `skills/vendor/` 樹住在
`skills/` 底下，不是 repo 根目錄。

!!! warning "常見陷阱 (Common pitfall)"
    把 `.claude-plugin/marketplace.json` 放在 repo 根目錄、
    然後用帶 subpath 的指令調用 CLI，會靜默地停用分組 ——
    根目錄的檔案永遠不會被讀，每個 skill 都會落到 **Other**。
    讓 manifest 的位置匹配安裝指令的 subpath。

## Manifest 形狀

參考：官方
[marketplace manifest schema](https://code.claude.com/docs/en/plugin-marketplaces)。

```json
{
  "name": "<unique-marketplace-id>",
  "owner": { "name": "...", "email": "..." },
  "metadata": {
    "description": "...",
    "version": "1.0.0",
    "pluginRoot": "./"
  },
  "plugins": [
    {
      "name": "<group-name-kebab-case>",
      "description": "Short description of the plugin / category",
      "category": "<for Claude Code /plugin UI>",
      "tags": ["...", "..."],
      "source": "./",
      "strict": false,
      "skills": [
        "./relative/path/to/skill-dir",
        "./another/skill-dir"
      ]
    }
  ]
}
```

`npx skills` picker 實際上消費的：

| 欄位 | 給 `npx skills` 用？ | 給 Claude Code `/plugin` UI 用？ |
|---|---|---|
| `metadata.pluginRoot` | yes (解析 `source`) | yes |
| `plugins[].name` | **yes — 驅動分組標頭文字** | yes |
| `plugins[].source` | yes (必須是以 `./` 開頭的字串；object/remote source 會被跳過) | yes |
| `plugins[].skills[]` | yes (必須以 `./` 開頭) | yes |
| `plugins[].description` / `category` / `tags` / `version` / `strict` | **no — pass through** | yes |

所以 `category` 跟 `tags` 目前算是免費的 metadata：放進 manifest
不花成本，未來任何原生消費者（Claude Code 的 `/plugin` 瀏覽器、
下游 catalog 工具）可以用它們，我們不用搬移檔案。

### picker 對每個 skill 列實際顯示什麼

依
[`src/add.ts`](https://github.com/vercel-labs/skills/blob/main/src/add.ts)
（`groupMultiselect` 呼叫），每個 skill 列被建構為：

```ts
{
  value: s,
  label: getSkillDisplayName(s),        // = s.name (SKILL.md frontmatter)
  hint:  s.description.slice(0, 57)+'…' // = SKILL.md description, truncated to 60 chars
}
```

所以使用者每個 skill 看到的**只有** SKILL.md 的 `name` + 截斷的
`description`。**`marketplace.json` 中沒有任何東西會 per-skill 顯示**
—— 不是 `plugins[].description`，不是 `category`，不是 `tags`，什麼都不是。
plugin 的 `name` 只會以分組標頭出現在 skill 列上方。

意思是：如果你想對 picker 中單一 skill 加註解 / 改標籤 /「標為棄用」/
覆寫 description，**SKILL.md 本身是唯一的旋鈕 (knob)**。catalog manifest
中沒有「外部註解」機制。

## 分組標頭渲染 —— `kebabToTitle`

picker 把每個 plugin `name` 用連字號 (hyphen) 切開、每個 token 做
titlecase，組成標頭文字。所以：

| `plugins[].name` | UI 標頭 |
|---|---|
| `document-skills` | Document Skills |
| `claude-api` | Claude Api |
| `ml-workflow` | Ml Workflow |
| `fullstack-nextjs` | Fullstack Nextjs |
| `notebooks` | Notebooks |

挑 titlecase 起來能讀的名字。`claude-api` → "Claude Api" 是官方
upstream 的選擇，現役在 `anthropics/skills` 的使用者介面中出現，
所以彆扭的 casing 是已知怪癖；不要用奇怪的 name 欄位來繞過。

## "Other" —— 自動 fallback 分組

CLI 在搜尋根目錄底下發現的 SKILL.md，**只要不在**任何
`plugins[].skills[]` 條目中，都會出現在 **Other** 分組標頭底下。
這就是為什麼 `anthropics/skills` 的 `template-skill` 落在 "Other"
—— 因為它沒被列在他們 manifest 的 `plugins[]`。

利用這點：暫時不適合任何分類的 skill，可以單純從 `marketplace.json`
省略，它仍然會被安裝，只是落在 "Other"。我們的 `make marketplace`
validator 對沒列出的 on-disk skill 發 warning（不是 error），
這樣容易注意到。

## 路徑解析規則（陷阱）

- `source: "./..."` 跟 `skills[]: "./..."` 是**相對於 marketplace 根目錄**
  （含 `.claude-plugin/` 的目錄）的路徑，不是相對於 JSON 檔案本身或
  `.claude-plugin/` 目錄。
- CLI 拒絕任何不以 `./` 開頭的路徑 —— `../` 跟絕對路徑都不允許
  （路徑遍歷保護 (path-traversal protection) 在
  [`isContainedIn`](https://github.com/vercel-labs/skills/blob/main/src/plugin-manifest.ts)）。
- `metadata.pluginRoot`（可選）會被前置 (prepend) 到每個 plugin 的
  `source`。我們沒用它；我們在每個 plugin 設 `source: "./"`，這樣
  每個 plugin 路徑直接解析在 manifest 根目錄底下 (`skills/`)。

## 保留的 marketplace `name`

依官方文件，這些不能用作 `name` 欄位：

- `claude-code-marketplace`、`claude-code-plugins`、
  `claude-plugins-official`
- `anthropic-marketplace`、`anthropic-plugins`
- `agent-skills`
- `knowledge-work-plugins`、`life-sciences`
- 任何冒充官方 marketplace 的名字
  （例如 `official-claude-plugins`、`anthropic-tools-v2`）

這個 repo 的 manifest 使用 **`daviddwlee84-skills`** —— GitHub repo
資料夾仍然可以叫 `agent-skills`；只有 manifest 內的 `name` 欄位被限制。
validator script 會強制這條。

## Versioning

- 如果 `metadata.version` **省略**且 marketplace 是 git-hosted，
  每個 commit 都被當成新版本 —— 使用者永遠看到 `main` 上的東西。
  這跟 `anthropics/skills` 一致。
- 如果 `metadata.version` **有設**，使用者只在數字改變時看到更新
  （semver 風格）。

我們目前設 `metadata.version: "1.0.0"` 當作基線。要切到「每個 commit
都是 latest」的語義，就拿掉這個欄位。

## `marketplace.json` vs `plugin.json`

| 檔案 | 目的 | 何時使用 |
|---|---|---|
| `.claude-plugin/marketplace.json` | 多個 plugin / 分類的 catalog | 多分類集合（這個 repo、`anthropics/skills`） |
| `.claude-plugin/plugin.json` | **單一** plugin 的 manifest | 單一 plugin 的 repo（一捆 skill，沒分組） |

兩個檔案不是冗餘的。`anthropics/skills` 只出貨 `marketplace.json`；
我們做一樣的事。一個 repo 技術上可以兩個都出貨，但對於這種多分類
catalog 來說，`plugin.json` 是不必要的。

## Cross-agent portability

`npx skills` 是個單向安裝器：它讀 manifest，然後把 SKILL.md 檔案
複製到每個目標 agent 的原生 skills 目錄（支援的目標列在
[`src/types.ts`](https://github.com/vercel-labs/skills/blob/main/src/types.ts)）。
其他 agent (OpenCode、Codex、Cursor、Aider、…) **不會**原生讀
`.claude-plugin/marketplace.json` —— 它們有自己的慣例
(`.opencode/`、`AGENTS.md`、`.cursor/rules/` 等)。

所以取捨是：

- 一個 `marketplace.json` 對於透過 `npx skills add` 做 cross-agent
  **install** 是夠用的。
- 在非 Claude agent 中做原生發現需要那個 agent 期望的東西，跟這個
  manifest 分開。

如果哪天我們需要第二種原生 catalog 格式，最乾淨的中介方案是把
`marketplace.json` 當成由 canonical YAML **生成 (generated)** 的產物，
並加一個 generator script。我們還沒這樣做 —— 單一消費者手動編輯目前是 OK 的。

## 不刪除而是隱藏 / 棄用 (deprecate) 一個 skill

CLI 透過 SKILL.md frontmatter 內建一個隱藏機制 —— 設
`metadata.internal: true`，skill 在 picker 中變不可見，但留在 repo 內。

依 [`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts)：

```ts
const isInternal = data.metadata?.internal === true;
if (isInternal && !shouldInstallInternalSkills() && !options?.includeInternal) {
  return null;
}
```

```yaml
---
name: my-deprecated-skill
description: ...
metadata:
  internal: true   # <- 把這個 skill 從 `npx skills add` picker UI 隱藏
---
```

這做的事：

- ✅ Skill 留在 repo，檔案不變。
- ✅ 預設從互動 picker 隱藏。
- ✅ 直接請求仍可安裝：`npx skills add <repo> my-deprecated-skill`
  傳 `includeInternal: true` 所以按名字查找會找到它。
- ✅ 進階使用者覆寫：`INSTALL_INTERNAL_SKILLS=1 npx skills add ...`
  也會把 internal skill 顯示在 picker 中。
- ✅ 與其他地方的發現相容 (Claude Code 的自動發現、這個 repo 的
  docs 站) —— `metadata.internal` 只是 `npx skills` 慣例。

把 skill 標為 internal 時，也要**從 `marketplace.json` 的
`plugins[].skills[]` 移除它的路徑** —— 不然你會有指向一個隱藏 skill
的死 catalog 條目。同一個 skill 不應該同時有這兩種設定。

### 為什麼不直接刪？

用 `metadata.internal` 而不是刪除的理由：

- 保留 docs 頁面可達 (skill 仍會在 docs 站渲染)。
- 為 vendored skill 保留 `vendor.yaml` 歷史與 `last_sync` 日期。
- 在棄用寬限期 (deprecation grace period) 允許按名字 opt-in 安裝。
- 為未來 debug 保留 `git log` / `git blame` 連續性。

如果你想要永久消失，刪除目錄、從 `marketplace.json` 移除條目、
（vendored skill 的話）也從 `vendor.yaml` 移除。

### Validator 涵蓋範圍（今日）

`scripts/validate-marketplace.sh` 目前**不**解析 SKILL.md frontmatter，
所以它不會抓出「internal skill 被列在 `marketplace.json`」這種錯誤。
如果我們在實務上撞到這個問題，validator 可以擴充成：

1. 解析每個 SKILL.md 的 frontmatter（例如透過 `yq` 或 python-frontmatter）。
2. 如果 `plugins[].skills[]` 中的任何路徑解析到帶 `metadata.internal: true`
   的 skill 就 error。
3. 對 internal skill 跳過「fall under Other」的 warning（它們根本不會
   在 picker 出現，所以 warning 是誤導的）。

這是個延期的增強 —— 看 TODO，當變得值得做時再說。

## 在這個 repo 裡操作 manifest

```bash
# 驗證 manifest（解析、name 沒被保留、所有路徑存在、
# 沒重複、on-disk skill 都有覆蓋）。
make marketplace

# 或直接跑 script 取得 verbose 輸出。
bash scripts/validate-marketplace.sh
```

加入新的 local 或 vendored skill 後：

1. 一如往常把 SKILL.md 放在 `skills/local/<name>/` 或
   `skills/vendor/<name>/`。
2. 打開 `skills/.claude-plugin/marketplace.json`，把新路徑（相對於
   `skills/`）加到對應 plugin 的 `skills[]` 陣列中，**或者**故意省略
   讓它落到 "Other"。
3. 跑 `make marketplace`。它會對沒列出的 skill 發 warning、對壞掉的
   路徑發 error。

## 原始碼參考

- `npx skills` package 原始碼：
  [vercel-labs/skills](https://github.com/vercel-labs/skills) on GitHub，
  npm package
  [`skills`](https://www.npmjs.com/package/skills)。
- Manifest 讀取邏輯：
  [`src/plugin-manifest.ts`](https://github.com/vercel-labs/skills/blob/main/src/plugin-manifest.ts)。
- Subpath + searchPath 邏輯：
  [`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts)。
- Picker UI 分組：
  [`src/add.ts`](https://github.com/vercel-labs/skills/blob/main/src/add.ts)
  （搜尋 `groupMultiselect` 與 `kebabToTitle`）。
- 官方 Claude Code 文件：
  [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)、
  [plugins-reference](https://code.claude.com/docs/en/plugins-reference)。
- 這個 repo 的參考 manifest：
  [`skills/.claude-plugin/marketplace.json`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/.claude-plugin/marketplace.json)。
