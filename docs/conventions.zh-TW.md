# Conventions — 慣例

!!! note "Terminology rule (zh-TW pages)"
    技術名詞首次出現以「中文 (English original)」格式呈現，例：依賴注入
    (dependency injection)。**不自創翻譯**——若無公認譯名直接保留英文
    （如 `embedding`、`tokenizer`）。代碼、API 名、CLI flag、套件名、檔名一律不翻。

這些是這個 repo 中每一個 local skill 都遵守的規則。它們存在的目的：
讓透過 `npx skills` 出貨的 package 維持可預測，新增 skill 是個機械式
(mechanical) 的動作，而不是一場設計練習。

## Local skill 佈局 (layout)

每個 `skills/local/<skill>/` 目錄應該包含：

- **`SKILL.md`** —— 必要檔案，包含 YAML frontmatter（`name`、`description`）
  以及遵循
  [agentskills.io best practices](https://agentskills.io/skill-creation/best-practices)
  的內文（精簡的 SKILL.md，控制在 ~500 行以內；偏好預設值勝過選單；
  程序 (procedure) 勝過宣告 (declaration)）。
- **`assets/`** —— skill 會複製到目標 project 的樣板 (template)
  （例如 `TODO.md.template`、`pitfall-doc.md.template`）。
- **`scripts/`** —— agent 應該調用的可執行輔助 script，避免在對話裡
  重新實作邏輯。Bash 3.2 相容（這樣才能在沒裝 homebrew bash 的
  原生 macOS 上跑）。
- **`references/`** —— agent 按需載入的長篇資料（決策表、schema
  快查表、anti-pattern 列表）。把細節推到這裡，避免 `SKILL.md` 變肥。

## 把 script 鏡射 (mirror) 到頂層 `scripts/`

當一個 skill 出貨的 script 同時也是這個 repo 自己想直接跑的（目前只有
[`project-knowledge-harness`](skills/project-knowledge-harness.md)），
就把它複製到頂層的 [`scripts/`](reference/scripts.md) 目錄，這樣
`make` target 跟 CI 才能直接調用。canonical 副本仍然保留在 skill 內，
這樣透過 `npx skills` 出貨的 package 才能保持自包含 (self-contained)。

這對副本必須維持 byte-identical。repo 目前還沒在 CI 強制檢查；
你改一邊，要在同一個 commit 內改另一邊。

## Vendor skill 佈局

`skills/vendor/<skill>/` 完全鏡射 upstream 的佈局。**不要在原地編輯**
vendored skill —— 修改會被 `make sync` 蓋掉。如果你需要客製化某個 vendored
skill，把它 fork 到 `skills/local/`，然後更新
[`vendor.yaml`](https://github.com/daviddwlee84/agent-skills/blob/main/vendor.yaml)
拿掉那個 upstream 條目。

## 文件 (Documentation)

每個 local skill 也應該在 `docs/skills/<skill>.md` 有一頁。skill 的
`SKILL.md` 是給 agent 看的（精簡、針對機器）；`docs/skills/<skill>.md`
是給準備決定要不要用它的人看的。兩個介面 (surface) 都有價值 —— 不要
試圖把它們合併。

Agent 按需載入的長篇 reference (`skills/local/<skill>/references/*.md`)
當受眾擴及瀏覽 docs 站的人時，可以鏡射或摘要到 `docs/reference/`，
但 canonical 副本仍然放在 `SKILL.md` 旁邊。

## 個人塗鴉區 (scratch area)

repo 根目錄的 `Collections.md` 跟 `notes/` 是維護者的個人塗鴉空間，
**刻意**不在發布的 docs 站、也不在 agent 看得到的介面內。不要從
`SKILL.md` 或任何 docs 頁面連結進去。
