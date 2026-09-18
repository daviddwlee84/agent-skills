# security-audit（vendored）

從 Cloudflare 的
[`cloudflare/security-audit-skill/skills/security-audit`](https://github.com/cloudflare/security-audit-skill/tree/main/skills/security-audit)
skill vendor 而來，採 MIT 授權。它是 Cloudflare 漏洞探索 harness 的單一 repo
起點（見
[Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness)）。
它透過 `vendor.yaml` 同步，`license_path: LICENSE` 會把 repo 根目錄的授權複製為
`LICENSE.txt`。不要在本機編輯 vendored 檔案，因為 `make sync` 會覆寫它們。

## 教什麼

這個 skill 讓 agent 成為防禦性、以原始碼為先的安全審查者。只有跨越真實信任邊界
的問題才算 finding：agent 必須指出低信任的 principal、輸入、被繞過的控制、受影響
的資源與觀察到的結果，然後提出能封住漏洞的最小原始碼修正。

它有兩種運作模式：

- **Guidance mode**（預設）用於安全問題、局部審查與 triage。agent 只使用相關
  段落，不寫任何稽核檔案。
- **Full audit mode** 只在使用者明確要求 audit、pen test、完整審查或報告產物時
  執行。共六個階段：reconnaissance、coverage-led hunting waves、候選驗證、結構化
  `findings.json`、獨立紀錄驗證，以及與目標無關的報告。輸出放在目標 repo 之外，
  預設為 `~/security-audit-skill/<repo>/run-<N>`。

## 安全模型

讀取原始碼永遠允許。目標程式碼只能在 OS 強制的 sandbox 內執行：無外部網路、
環境變數採 allowlist、目標唯讀、資源有硬上限。若無法強制 sandbox，agent 不執行
程式碼，改記錄一筆 `needs_validation` blocker。此 skill 禁止探測已部署的 endpoint、
共享基礎設施或真實身分。

## 附帶檔案

| 檔案 | 用途 |
|---|---|
| `RECONNAISSANCE.md`、`HUNTING.md`、`VALIDATION-AND-REPORTING.md` | 各階段指示與 sub-agent prompt |
| `ATTACK-CLASSES.md` + 10 份領域 companion | web/auth、client-side、AI/LLM、memory safety、supply chain、cloud、RPC、資源耗盡、資料隔離、desktop/mobile IPC 的 hunting class |
| `report-schema.json` | `confirmed` / `needs_validation` / `rejected` 紀錄的 schema |
| `validate-findings.cjs`、`validate-coverage-ledger.cjs` | 零依賴的 Node validator，附 `*.test.cjs` 測試 |

validator 只需要 Node。要檢查同步後的副本，在 skill 目錄執行
`node --test validate-findings.test.cjs validate-coverage-ledger.test.cjs`。

## Canonical SKILL.md

完整指示見
[`skills/vendor/security-audit/SKILL.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/vendor/security-audit/SKILL.md)。
