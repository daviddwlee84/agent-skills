# demo-evidence

讓 agent **留下驗收證據** —— 針對它剛做完的 feature,把截圖、螢幕/終端錄影、
HTTP log 歸檔到受 `.gitignore` 保護的 `.evidence/` 目錄,讓人(或之後的 agent)
可以**非同步驗收**,不必再讀 diff 或手動啟動 app 重試。這就是 Cursor
「Demos over diffs」的概念,但完全在本機且不污染 git。

每個 **bundle** 都關聯到產生它的 coding-agent session,以及擷取當下的
git branch/commit,並透過 `manifest.json`(機器可讀)+ `MANIFEST.md`
(人看的驗收頁)自我描述。

## 目錄結構

```
.evidence/                                   # 被 gitignore(根 .gitignore 一條規則)
  claude-5f932f43/                           # <agent>-<session>
    2026-07-07T11-11-29Z-6526681-login-flow/ # <UTC-ts>-<shortSHA>[-<title>]
      manifest.json
      MANIFEST.md
      login.png / login.webm / login-trace.zip
      run.log
      http/health.txt
```

## 生命週期(三支腳本)

1. **`new-bundle.sh`** —— 開一個 bundle:偵測 agent session + git
   branch/short-SHA/dirty,建立目錄、產生 manifest 骨架、確保 `.evidence/`
   已被 gitignore,並記錄 `.evidence/.current`。
2. **`capture.sh <web|term|http|screen>`** —— 每種介面擷取一個 artifact,
   並寫進 `manifest.json`:
   - `web` → Playwright 整頁截圖 + 影片 + trace
   - `term` → asciinema 錄製(沒有時退回 tee 的純 log)
   - `http` → curl 狀態碼 + headers + body + 耗時
   - `screen` → ffmpeg 螢幕錄影(macOS avfoundation / Linux x11grab)
3. **`finalize.sh`** —— 蓋上結論(`PASS`/`NEEDS_WORK`)、補上重現步驟、
   刷新 artifact 大小、可選地掃描文字 artifact 的機密,並產生 `MANIFEST.md`
   驗收頁。

```bash
NB=skills/local/demo-evidence/scripts
BUNDLE=$(bash $NB/new-bundle.sh --title "login flow" --feature "login 導向 /dashboard" | jq -r .bundle_dir)
bash $NB/capture.sh term --cmd "mytool --demo" --name run
bash $NB/capture.sh http --url http://localhost:8000/health --name health
bash $NB/finalize.sh --verdict PASS --step "開 /login" --step "送出帳密" --scrub
```

## 何時用 / 何時不用

當使用者想對 agent 的成果做**非同步驗收 / sign-off**、說「錄個 demo」、
「留下證據」、「證明它會動」,或 reviewer 說「給我看它能動」而不想讀 diff 時,
就用它。沒有 runtime 表面的改動(純文件、被測試覆蓋的重構)就跳過 —— 沒東西可 demo。

## 已知限制(v1)

- **`.evidence/` 的媒體無法內嵌進 GitHub PR** —— 被 gitignore 的檔案沒有公開
  URL。PR 貼圖(文字 manifest + gist raw URL 內嵌圖片)是已登記的 `P?` backlog,
  v1 不做。
- **截圖/影片無法自動去敏** —— `finalize.sh --scrub` 只用 gitleaks 掃文字
  artifact 並回報;其餘要人工過目後才對外分享。
- **`capture.sh web` 需要專案裝 Node + Playwright**;`screen` 需要 ffmpeg
  (macOS 還需螢幕錄製權限)。

## 標準 SKILL.md

完整的觸發描述、工作流程、腳本旗標/退出碼與陷阱,請見
[skills/local/demo-evidence/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/demo-evidence/SKILL.md)。
