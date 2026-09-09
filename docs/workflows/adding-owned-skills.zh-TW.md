# 新增 owned skill

當 skill 應該跟著你維護的另一個專案演進時，使用 `owned`。
來源專案負責維護 canonical；這個 collection 提供探索、分組安裝、文件與經過檢查的分發副本。

| 分類 | Canonical 位置 | 修改規則 |
|---|---|---|
| `local` | 本 repository | 修改 `skills/local/<name>/` |
| `owned` | 自己的另一個 repository | 在來源修改，同步到 `skills/owned/<name>/` |
| `vendor` | 第三方 repository | 跟隨 upstream，同步到 `skills/vendor/<name>/` |

分類由 `collection: owned` 明確宣告，不從 GitHub username 猜測。
`vendor.yaml` 保留歷史檔名，作為兩類 upstream 的共用 manifest；省略 `collection`
仍然是原有 vendor 行為。兩類都支援 `series`、`license_path` 與 `frozen`。

## 先在來源專案建立

若 skill 適合開發該專案時使用，canonical 放在 `.agents/skills/<name>/`，
可用 `.claude/skills/<name>` discovery symlink 讓 Claude Code 也載入。
呼叫 `skill-author` 時明確指定 project scope：

```bash
bash skills/local/skill-author/scripts/new-skill.sh \
  --project --root /path/to/source-project userscript-development
```

在來源專案完成撰寫與驗證，發布 canonical 後，再從這個 collection 加入遠端同步：

```bash
./scripts/add-vendor.sh --owned \
  daviddwlee84/Tampermonkey-Scripts/.agents/skills/userscript-development
```

在 marketplace 對應 plugin 的 `skills[]` 加入 `./owned/userscript-development`，
補齊雙語文件與導覽，執行 `make validate` 與 `make docs-build`。
有 series 時，路徑是 `./owned/<series>/<name>`。

## 第一次 upstream 還沒發布時

跨兩個本機 repo 撰寫的新 skill，尚無包含新檔案的遠端 commit。
不要把無關的 HEAD 寫成 `last_sync`。只在這個首次建立階段：

1. 完成並驗證來源專案的 canonical 目錄。
2. 把實際檔案複製到 `skills/owned/<name>/`，核對兩邊逐檔相同。
3. 在 manifest 加入來源、`collection: owned`、`pending_upstream: true`，
   並讓 `last_sync.date`／`last_sync.commit` 留空。
4. 持續在來源專案開發，需要時刷新首次分發副本。

```yaml
skills:
  - name: userscript-development
    collection: owned
    pending_upstream: true
    upstream:
      owner: daviddwlee84
      repo: Tampermonkey-Scripts
      path: .agents/skills/userscript-development
      branch: main
    last_sync:
      date: ""
      commit: ""
```

一般 `make sync`／`make sync-check` 會明確回報 pending，保留現有副本。
來源發布後，啟用該條目：

```bash
./scripts/sync-vendor.sh --activate userscript-development
```

啟用會真正從遠端同步，成功後才移除 pending。來源路徑未發布或下載失敗時，
原有副本不會被刪掉。檢查 diff 後，再發布此 collection。
Pending 表示自有來源尚未首次發布；`frozen` 則表示刻意停止跟隨某個 upstream。

## 平常更新循環

1. 修改來源專案時，同步更新並驗證 canonical skill。
2. 依來源專案的流程發布變更。
3. 在這裡先跑 `./scripts/sync-vendor.sh --check userscript-development`，
   再跑 `./scripts/sync-vendor.sh userscript-development`。
4. 檢查鏡射 diff 與 upstream SHA，跑發布檢查，再依正常流程發布 collection。

既有每週同步 workflow 也會處理已啟用的 owned skill，並建立供審查的 PR。
同步器以記錄的 commit 取得 skill tree，先暫存完整下載，再替換上一份可用副本。

分發副本必須是實際檔案；跨 repo symlink 會指向下游不存在的位置。
不要另建 `skills/local/<name>` 當第二份 canonical，也不用在本 collection 的
discovery 目錄啟用這個 skill，除非維護此 collection 本身需要它。

發布後可從 collection 的分組 picker 安裝，也可直接從來源專案安裝。
Skill 名稱仍是 `userscript-development`；切換 upstream 來源時仍應檢查 lockfile，
必要時明確重新安裝。

## 維護工具驗證

`make test-source-sync` 使用假的 GitHub CLI 與真的 `yq` 執行離線測試：
預設 vendor 路徑、owned／series、check 模式、pending 啟用、失敗保留副本、
frozen、目錄驗證，以及 `add-vendor.sh --owned`。需要 Python 3 與 mikefarah/yq。
