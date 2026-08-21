# Adding vendor skills — 加入 vendor skill

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

Vendor skill 是從 upstream repo 精選 (cherry-picked) 進
[`skills/vendor/`](https://github.com/daviddwlee84/agent-skills/tree/main/skills/vendor)
的第三方 skill。
[`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
這個 manifest 追蹤每個 upstream 來源、最後同步日期、commit SHA，
讓重新同步可重現。

## 快速加入 (Quick add)

```bash
./scripts/add-vendor.sh owner/repo/path/to/skill

# Examples
./scripts/add-vendor.sh marimo-team/skills/skills/marimo-notebook
./scripts/add-vendor.sh vercel-labs/agent-skills/skills/next-js
./scripts/add-vendor.sh --name my-name --branch dev owner/repo/skills/some-skill

# 用 series 子目錄分組 (group)
./scripts/add-vendor.sh --series fullstack-nextjs vercel/vercel-plugin/skills/nextjs

# 或透過 Makefile
make add-vendor SOURCE=owner/repo/path/to/skill

# GitHub URL 也可以
./scripts/add-vendor.sh https://github.com/marimo-team/skills/tree/main/skills/marimo-notebook
```

這會驗證 upstream 路徑存在、把條目寫進 `vendor.yaml`、並立即同步該
skill。傳 `--no-sync` 可以只新增條目而不下載。

**依賴項目 (Dependencies)：** `gh`（已認證的 GitHub CLI）跟 `yq`
（YAML processor）。

## Series 分組 (grouping)

當你要 vendor 一組圍繞同一個技術組合 (stack) 的 skill（例如 Next.js +
Supabase + shadcn），傳 `--series <name>`，這樣 skill 會落到
`skills/vendor/<series>/<name>/` 而不是平鋪 (flat) 結構。`series`
欄位記錄在 `vendor.yaml`，`sync-vendor.sh` 會尊重它。

```yaml
# vendor.yaml
- name: nextjs
  series: fullstack-nextjs              # ← 可選，省略代表平鋪佈局
  upstream:
    owner: vercel
    repo: vercel-plugin
    path: skills/nextjs
    branch: main
  last_sync: { date: "...", commit: "..." }
```

結果是 `skills/vendor/fullstack-nextjs/nextjs/SKILL.md`。
`npx skills@latest add` 的探索做 5 層 fallback 遞迴搜尋，
所以 series 子目錄一樣會被找到。

既有的平鋪條目（沒有 `series` 欄位）行為不變。這個 repo 目前活躍的 series：

- **`fullstack-nextjs`** —— 詳見 [Skills 總覽 > Fullstack Next.js series](../skills/index.md#fullstack-nextjs-series)

## Repo 層級授權檔

若 skill subtree 本身沒有包含 upstream license，請在 manifest entry 加上
`license_path`：

```yaml
- name: my-skill
  upstream:
    owner: org-name
    repo: project
    path: skills/my-skill
    branch: main
  license_path: LICENSE
  last_sync:
    date: ""
    commit: ""
    license_sha: ""
```

同步腳本會將它複製成 `skills/vendor/<name>/LICENSE.txt`，並獨立記錄 blob
SHA，因此 `make sync-check` 也能偵測只有授權檔發生的更新。

## 手動 config

如果你比較想直接編輯 `vendor.yaml`：

```yaml
- name: my-skill
  upstream:
    owner: org-name
    repo: skills-repo
    path: skills/my-skill
    branch: main
  last_sync:
    date: ""
    commit: ""
```

接著跑 `make sync` 下載並寫入 `last_sync` 戳記。

## 檢查 upstream 是否有更新

```bash
make sync-check
```

這會對每個條目記錄的 `last_sync.commit` 做 dry-run，並印出哪些 skill
有 upstream 新 commit。跑 `make sync` 套用更新。

## 為什麼不直接從 upstream 安裝？

`npx skills add owner/repo/path/to/skill` 一次只裝一個 skill，
而且不留 manifest。把 skill vendor 進這個 repo 帶來：

- 整套精選集合的單一安裝指令
  (`npx skills@latest add daviddwlee84/agent-skills/skills`)。
- 每個 skill 都鎖定 (pin) 某個 commit，避免上游粗糙更新時被打到。
- 重新同步時 repo 會出現 diff，那就是你閱讀這次變更、決定要不要接受
  的時機。

## 不要在原地編輯 vendored skill

`skills/vendor/` 底下的修改會被 `make sync` 蓋掉。如果你需要客製化
某個 vendored skill，把它 fork 到 `skills/local/`，然後從
`vendor.yaml` 拿掉那個 upstream 條目。詳見
[Conventions](../conventions.md)。
