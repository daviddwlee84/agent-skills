# nautilus-trader

協助 agent 撰寫、除錯、審查與遷移使用 **NautilusTrader** 的程式碼，包含 Python
（`nautilus_trader`）與 `nautilus-*` Rust crates。此 local skill 與
[vectorbt](vectorbt.md)、[quantatitive-factor-researcher](quantatitive-factor-researcher.md)
同屬 `quantitative-finance` marketplace group。

NautilusTrader 正處於世代交替。舊的 Cython 核心（v1，`1.x`，最後一版 1.231.0）
與 Rust 核心 + PyO3 綁定（v2，`2.0.0rcN`）都以 `nautilus_trader` 安裝與 import，
但 Python API 差異很大。2.0 仍是 release candidate 期間，不加 `--pre` 的
`pip install nautilus_trader` 會裝到 v1，官網 `latest` 文件卻寫的是 v2，
v1 文件也已不再 host。因此 skill 先辨識世代與確切版本，再從對應 git tag 讀文件。

向量化訊號研究與參數掃描仍交給 VectorBT。這份 skill 負責事件驅動回測
（order book、fill／latency model），以及同一份策略程式碼接到 sandbox、testnet
與實盤 node，並透過 adapter 串接交易所與資料來源。

## 內容

- 精簡入口，外加按需讀取的 references：世代與安裝、v1 → v2 遷移對照、
  實盤／sandbox、Rust crates、官方來源。
- `nt_context.py doctor`：檢查專案 Python，回報以下資訊：
  - 已安裝版本與 native core（`cython` 或 `pyo3`）；
  - lock／requirements pin 與 `nautilus-*` crates；
  - import `nautilus_trader` 的程式碼中只屬於 v1 或 v2 的名稱；
  - PyPI stable 與 pre-release 狀態；
  - 附文件 git ref 與衝突項目的建議。
- `nt_context.py docs`：以 sparse、partial 的 `git clone` 將某個 tag／branch 的
  `docs/`、`examples/`、`MIGRATION_V2.md`、`RELEASES.md`、`ADAPTERS.md`、`ROADMAP.md`
  放進 XDG 快取；不需要 GitHub token，不佔 API 配額，也不需要 embeddings。
- 實盤安全關卡：連接真實帳戶、使用憑證、在非 sandbox 環境下單，都需使用者明確授權；
  一律先走 sandbox／testnet。
- 使用本地 git remote、合成套件與 PyPI JSON 的離線測試。

原始碼：[local skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/nautilus-trader)。

## 使用

以下命令相對於已安裝的 skill 目錄，需要 macOS／Linux 上的 Python 3.11+ 與 git。

```bash
python3 scripts/nt_context.py doctor --project /path/to/project --python /path/to/env/bin/python
python3 scripts/nt_context.py docs --project /path/to/project --python /path/to/env/bin/python
# 只查文件：明確指定 tag 或 branch
python3 scripts/nt_context.py docs --ref v2.0.0rc5
```

用 `rg` 搜尋回傳的 `docs_dir` 與 `examples_dir`，讀完整的頁面或範例，再到專案
interpreter 核對 signature。範例 tag 並非固定預設。

## 世代對照

| | v1 | v2 |
|---|---|---|
| 版本 | `1.x`（最後一版 1.231.0） | `2.0.0rcN` |
| 核心 | Cython（wheel 內含 `.pyx`／`.pxd`） | Rust，`nautilus_trader._libnautilus` |
| 實盤 node | `TradingNode` + config dict | `LiveNode.builder(...)` |
| Config | msgspec `Struct` | PyO3 型別 |
| Branch／文件 | `develop_v1`，只有 git tag | `develop`，官網 `latest`／`nightly` |

既有 v1 專案保持原樣；新專案建議使用 v2 並 pin 確切版本，同時明確標示 RC 狀態。
上游不建議在投入真實資金的實盤使用 release candidate。

## XDG 快取與同步

快取根目錄順序：`--cache-dir` → 絕對路徑的 `$XDG_CACHE_HOME/nautilus-trader-agent`
→ `~/.cache/nautilus-trader-agent`。每個 ref 存在 `refs/<ref>/`，manifest 以原子方式
切換，generation 建立後不再修改；切換後保留前一個 generation 一輪。

- Tag 不可變：快取後直接回 `cached`，不連網；`--refresh` 才比對遠端 peeled commit。
- Branch 超過 24 小時才用 `git ls-remote` 檢查，回 `unchanged` 或 `updated`。
- 遠端失敗但有有效快取時回 `stale`（exit 0），必須如實回報。`--offline` 只用有效快取；
  `--dry-run` 不寫入任何檔案。
- 不安裝背景排程。

## 驗證基準

2026-09-17 於 macOS ARM64、Python 3.12.10 驗證：

- `doctor` 在兩個獨立 uv 環境中正確辨識 `nautilus_trader` 1.231.0（`cython`）與
  2.0.0rc5（`pyo3`），並依即時 PyPI metadata 回報 `pre_flag_required: true`。
- `docs` 同步 `v1.231.0`（393 個檔案）與 `v2.0.0rc5`（353 個檔案）各約 8 秒；
  第二次執行回 `cached`，耗時 0.06 秒。
- v1／v2 名稱標記在 rc5 的 docs 與 examples 中沒有找到任何 v1 名稱；v1 tag 中的
  v2 命中只出現在 `interactive_brokers_v2` 預覽範例。
- rc5 quickstart 在全新的 v2 程序中跑出 902 筆 fills、451 個 positions；同一檔案在 v1
  失敗：`ImportError: cannot import name 'OrderSide' from 'nautilus_trader.model'`。
- v2 sandbox `LiveNode` 在沒有憑證的情況下成功 build、註冊策略並 dispose，全程未連接交易所。

以上是測試過的版本組合，不是依賴版本限制。

## 官方來源

- [文件](https://nautilustrader.io/docs/latest/)、[llms.txt](https://nautilustrader.io/docs/llms.txt) 與 [Python API reference](https://nautechsystems.github.io/nautilus_docs/python-api-latest/)
- [Repository](https://github.com/nautechsystems/nautilus_trader)、[`MIGRATION_V2.md`](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md) 與 [Releases](https://github.com/nautechsystems/nautilus_trader/releases)
- [PyPI](https://pypi.org/project/nautilus_trader/) 與 [crates.io](https://crates.io/crates/nautilus-model)
- 社群：[Discord](https://discord.gg/NautilusTrader) 與 [GitHub Discussions](https://github.com/nautechsystems/nautilus_trader/discussions)

撰寫時評估的社群 skill 都沒有授權條款，其中一份只支援 v1，因此這份 skill 採自行撰寫。
