# clash-proxy-api

透過 **Clash / mihomo** 執行中的 external-controller REST API，用自然語言操作代理
——例如「我現在走哪個節點？」「切到日本節點」「切成 global 模式」「開 TUN」「重載設定」
或「Clash API 連不上」。技能內建兩支腳本包裝 controller API 與作業系統系統代理，並附兩份
參考文件說明如何依用戶端啟用 API、以及原始端點清單。

| 介面 | 回答的問題 |
|---|---|
| `clash_api.py doctor` | 「controller 連得上嗎？連不上的話，要在哪個用戶端把 API 打開？」 |
| `clash_api.py status` | 「我目前的節點、模式、TUN 狀態、連接埠、代理群組是什麼？」 |
| `clash_api.py switch/mode/tun/reload/connections` | 「即時調整代理：選節點、切 rule/global/direct、開關 TUN、重載、關連線。」 |
| `clash_api.py delay/group-delay/proxies/rules` | 「測延遲、列節點/規則。」 |
| `clash_sysproxy.sh` | 「用戶端沒有系統代理開關時（mihomo CLI、無頭機、Ubuntu），直接切作業系統的系統代理。」 |
| `references/enable-api-by-client.md` | 「如何在 Verge Rev / ClashX / mihomo 開啟或找到 API 位址？System Proxy、TUN、Service Mode、Mixin 在哪裡？」 |
| `references/api-endpoints.md` | 「`/traffic`、`/providers`、`/dns/query` 這些要 curl 哪個端點？」 |

技能的核心原則是**不寫死任何假設**。controller 探索順序：`--controller`/`--secret`
→ `CLASH_CONTROLLER`/`CLASH_SECRET` 環境變數 → 選用的 Television hook → 本機設定檔 →
探測 `127.0.0.1:9090` 再 `:9097`（Clash Verge Rev）。第一個連得上的勝出。代理連接埠會從
即時設定讀取，而非假設是 `7890`。

## 何時觸發

- 「我走哪個節點/模式？」→ `status`；「把 PROXY 切到日本節點」→ 先 `delay` 再 `switch`。
- 「切成 global / rule / direct」→ `mode`；「開 TUN」→ `tun on --restart`。
- 「重載設定」「關掉所有連線」「查我的出口 IP」→ `reload` / `connections` / `egress`。
- 「Clash API 有開嗎？/ 壞了」→ `doctor`，再看 enable-API 參考文件。
- 「我 Ubuntu 上沒有系統代理開關」→ `clash_sysproxy.sh`。
- 用戶提到 Clash、mihomo、Clash Verge (Rev)、ClashX、external-controller、`9090`/`9097`，或用名稱指某個節點。

## 何時不適用

- 手改訂閱／規則 YAML——API 只做重載與切換，不負責撰寫設定；請改檔案後 `reload`。
- **Mixin / Merge** 設定——那是用戶端的設定檔功能（Clash Verge / CFW），不是執行期 API。技能會引導，但不代寫。
- 購買／挑選節點、管理訂閱。

## 結構

```
skills/local/clash-proxy-api/
├── SKILL.md                        # 約 177 行；intent→command 對照表 + 陷阱清單
├── scripts/
│   ├── clash_api.py                # 純標準函式庫 Python 3；controller API 客戶端
│   └── clash_sysproxy.sh           # bash 3.2；作業系統系統代理開關
├── references/
│   ├── enable-api-by-client.md     # 各用戶端×OS：啟用 API、System Proxy、TUN、Service Mode、Mixin
│   └── api-endpoints.md            # 完整端點清單 + 原始 curl 範例
└── agents/openai.yaml              # OpenAI 風格啟動描述檔
```

## 設計重點

- **`clash_api.py` 只用標準函式庫**——不需 `uv`、不需 pip，只要有 `python3` 就能跑（下游最實際的情況）。若能 import PyYAML 就用，否則用小型正規表達式掃描讀取所需的兩個設定鍵。
- **每個寫入操作都支援 `--dry-run`**；具破壞性的 `connections close --all` 需要 `--yes`；永遠不印出 secret（`status` 只說 `secret: yes/no`）。
- **結束碼用於分支重試邏輯**：`0` 成功、`1` 用法錯誤、`2` 群組/節點不存在（訊息會列出實際成員）、`3` controller 連不上、`4` 操作被拒。`clash_sysproxy.sh`：`0/1/2/3`。
- **三層模型**——controller API（可靠）、啟用/探索（API 關閉時）、API 做不到的 OS/用戶端開關（System Proxy、Service Mode、Mixin）。

## 技能內建的陷阱提醒

- controller **不一定是 `127.0.0.1:9090`**（Verge Rev 是 `9097`；GUI 會隨機挑埠；路由器在 LAN 上）——一律探索。
- 代理連接埠**不一定是 `7890`**——從 `status` 的 ports 讀取。
- **透過 API 開 TUN 需要有特權的核心**（Service Mode / root）且通常要 `POST /restart`；單純 `PATCH` 會回 204 但不會真的接管流量。
- **System Proxy 是作業系統設定，不是 API 概念**——用用戶端開關或 `clash_sysproxy.sh`。
- `group-delay` / `/providers` / `/restart` 是 **mihomo 專屬**（在傳統 Premium 核心上會 404）。

## 驗證

```bash
bash skills/local/skill-author/scripts/lint-skill.sh skills/local/clash-proxy-api   # 0 錯誤、0 警告
python3 skills/local/clash-proxy-api/scripts/clash_api.py doctor                     # 探索 + 診斷
python3 skills/local/clash-proxy-api/scripts/clash_api.py status                     # 對著真實 controller
bash   skills/local/clash-proxy-api/scripts/clash_sysproxy.sh detect                 # 唯讀查看系統代理狀態
```

讀取指令對真實 controller 是安全的；寫入指令（`switch`、`mode`、`tun`、`reload`、
`connections close`）可用 `--dry-run` 預覽。
