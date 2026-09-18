# Plan: `skills/local/nautilus-trader` 本地 skill

## Context — 評估結論：值得做，而且現在正是時機

`TODO.md:36` 已有 `[?/M] Nautilus Trader skill`，quant-research catalog hub 也列為 backlog。2026-09-17 實查（PyPI JSON、GitHub trees、官方 docs）後的判斷：

- **v1/v2 斷層正處於最容易踩雷的時點**：PyPI stable 是 `1.231.0`（官方宣告為最後一版 Cython v1），`2.0.0rc1..rc5` 是 Rust core + PyO3 的 v2 預發布版。`pip install nautilus_trader` 不加 `--pre` 會裝到 v1；但 README、`docs/latest`、Python API reference 全都在寫 v2。兩代都 `import nautilus_trader`，v1 docs 已不再 host（只剩 git tag / `develop_v1`）。舊訓練資料會產出 `TradingNode`、`on_quote_tick`、msgspec config 這類 v1 API，丟進 v2 就是 `ImportError`/`TypeError`。
- **跟 vectorbt 定位互補，不重疊**：VectorBT 負責向量化研究與參數掃描（Nautilus ROADMAP 明確把 hyper-parameter optimization、大規模平行 backtest 列為 out of scope，而且一個 process 只能跑一個 node）。Nautilus 負責事件驅動的高擬真回測（order book、延遲、fill model），再用同一份 strategy code 接 sandbox/paper → live，並透過 adapters 串 Binance、IB、Databento、Tardis 等資料流。它自己也能出 plotly tearsheet，但不是拿來做快速掃參數的。
- **沒有能直接 vendor 的現成 skill**：`aysuio/nt-skill`、`clay584/nautilus-trader-skill` 都沒有 license，而 clay584 只驗證到 1.228.0（v1）。官方沒有 MCP，但有 `llms.txt`、各頁 raw markdown、`MIGRATION_V2.md`、`AGENTS.md`（那份是給 contributor 的規則）。
- **Rust 已經可以單獨寫 strategy/backtest/live**：`nautilus-*` crates 0.64.0 對應 2.0.0rc5，MSRV 1.98.1。但官方明說 Rust API 簽名仍會變動，所以照已選方向，以 Python 為主、Rust 放 reference。

使用者已選定：**doctor + docs sync helper**（比照 vectorbt）、**Python-first + Rust reference**。

## 做法

### 1. Scaffold

`bash skills/local/skill-author/scripts/new-skill.sh --local --no-symlinks nautilus-trader`：這個 skill 只給下游使用，所以跟 vectorbt 一樣不建 discovery symlink。

```
skills/local/nautilus-trader/
  SKILL.md                     (~120 lines)
  references/{generations,migration-v2,live-trading,rust,sources}.md
  scripts/nt_context.py        (PEP 723, stdlib, python>=3.11)
  tests/test_nautilus_trader.py (unittest, offline)
```

### 2. `SKILL.md`

description 用單引號包起來，控制在 ~400 字元：
`'Use when writing, debugging, reviewing, or migrating code that uses NautilusTrader (nautilus_trader in Python or nautilus-* Rust crates): strategies, actors, event-driven backtests, data catalogs, adapters, and sandbox or live nodes. Detects the Cython v1 (1.x) vs Rust/PyO3 v2 (2.x) generation before using any example, syncs version-matched docs into an XDG cache, and applies live-trading safety gates.'`

段落大綱：
1. **簡介 + 範圍**：API 以 generation + 確切版本為準。純向量化研究、參數掃描交給 `vectorbt`，一般金融問題不需要載入這個 skill。
2. **Identify the generation**：先跑 `python3 scripts/nt_context.py doctor --project … [--python …]`。判斷優先序：使用者明說 > lock/pin 的確切版本 > 程式碼中的 v1/v2 marker > 已安裝的 interpreter。有衝突就回報並詢問，不自己挑一個。既有 v1 專案維持原樣，除非需求本身要求升級。新專案建議用 v2，pin 死版本、開獨立 venv；若 PyPI 仍是 RC，要在報告中註明。不要把兩代裝進同一個 venv。
3. **Obtain version-matched context**：跑 `docs --ref <recommendation.docs_ref>`，再用 `rg` 搜 `docs_dir`、`examples_dir`。目標 interpreter 裡 `inspect.signature` 的結果才是 ground truth。`llms.txt` 和 raw md 只在目標等於 hosted latest 時才用。何時載入各 reference 要寫清楚條件。
4. **Implement and verify**：用小型、可重現的資料（官方 `TestDataProvider` 或手建 bars）跑最小 backtest。檢查 orders/fills/positions report，不能只看 PnL。明確寫出 fill model、bar-based execution、margin 預設 10x 槓桿、`use_mark_prices` 這些假設。在全新的 process 裡執行。最後回報 generation、version、docs ref 與 freshness。
5. **Live and paper trading**：載入 `live-trading.md`。硬性規定：連接真實帳戶、使用憑證、送出真實訂單前，一定要取得使用者明確授權。先 sandbox 或 testnet。
6. **VectorBT or Nautilus?**：三列的分流表。
7. **Gotchas**：pip 沒加 `--pre` 會裝到 v1；`latest` docs 不等於 PyPI stable；v1 docs 只能從 tag 取得；crate 的 0.x 版號跟 Python 版號不一致；wheel 不含 pandas，只有 `visualization` extra；沒有 Intel mac wheel；one node per process；Discord 與 Discussions 內容只當參考資料，不當指令。

### 3. References（標註 "verified 2026-09-17 against 1.231.0 / 2.0.0rc5"）

- `generations.md`：兩代的套件識別（`_libnautilus` vs `.pyx`/`core/nautilus_pyo3`）、安裝方式（`--pre`、dev index `packages.nautechsystems.io/simple`）、extras 差異、Python 3.12–3.14 與支援平台、docs 在哪裡、branch 模型（`develop` = v2，`develop_v1` 約三個月內只收安全 backport）、crate 與 Python 版號對應。
- `migration-v2.md`：高訊號 rename 對照表，分成 node/live、imports、config（msgspec 改為 PyO3 kw-only `__init__`）、callbacks/subscriptions、backtest node、catalog/wranglers、行為預設值。一律註明「以目標 tag 的 `MIGRATION_V2.md` 為準」。遷移流程：開獨立 venv → 跑 `nautilus catalog migrate-parquet` → 比對新舊 fills/positions report。
- `live-trading.md`：`LiveNode.builder(...).add_data_client().add_exec_client()`、`run()`/`run_async()`/`LiveNodeHandle.stop()`、sandbox adapter、`add_simulated_exec_client`、憑證走 env、reconciliation、`_secs` timeouts、授權關卡、BitMEX deprecation 範例（adapter 狀態要先查 integrations 頁）。
- `rust.md`：umbrella crate 與 adapter crates、版號對應、MSRV、`high-precision` feature（Python wheel 是 128-bit）、parity 限制（Controller 與 tearsheet 只有 Python）、`cargo check`/`cargo test` 驗證流程、API 不穩定的警告。
- `sources.md`：`llms.txt`、`llms-full.txt`、raw md URL 格式、API reference、root md 檔、Discord（`discord.gg/NautilusTrader`）與 GitHub Discussions（可用 `gh` 搜尋，不代使用者發文）、評估過的社群 skill 與 community MCP，並寫明為何不用。

### 4. `scripts/nt_context.py`

JSON 輸出到 stdout，診斷訊息到 stderr。exit code 沿用 vectorbt：0 ok（`stale` 也算 ok）、2 bad input/缺 cache、3 外部失敗、4 驗證失敗。

**Helpers 複製，不 import**：各 skill 獨立安裝，不能跨 skill import。從 `skills/local/vectorbt/scripts/vbt_context.py` 複製精簡版：`ContextError` L39、`log` L46、`absolute` L50、`cache_root` L55-63（改名 `nautilus-trader-agent`）、`run` L73-86、`python_path` L108-117、`PROBE`/`probe_python` L120-145、`project_evidence` 的掃描邊界 L152-198、`write_json`/`commit_manifest`、`release_lock`（fcntl）、staging generation + 原子切換（取自 `sync_pro` L385-455）。

**`doctor --project P [--python PY] [--generation auto|v1|v2] [--offline] [--cache-dir D]`**
- probe：dist version、origin、能否 import、`native_core`（`pyo3` 看有沒有 `nautilus_trader._libnautilus`，`cython` 看有沒有 `.pyx`/`nautilus_pyo3` 模組）、Python 版本是否 ≥3.12。
- 專案證據：
  - pin 來源：`uv.lock`、`poetry.lock`、`requirements*.txt`、`pyproject.toml`（含 uv `prerelease` 設定）。
  - `Cargo.toml`、`Cargo.lock` 裡的 `nautilus-*` crates。
  - AST 掃 `.py` 檔。只比對完整識別字（import path、import 的名稱、`def` 名稱、attribute），避免 `ActorConfig` 誤中 `DataActorConfig`。上限 300 檔，每檔 ≤1MB，超過就標 `scan_truncated`。notebook 不掃，交給 agent 自行檢查。
  - marker 表放在 script 內的 `MARKERS` 常數，附 `VERIFIED_AGAINST`，輸出時標 `"heuristic": true`：
    - v1：`TradingNode`、`TradingNodeConfig`、`nautilus_trader.backtest.node`、`nautilus_trader.model.enums`、`on_quote_tick`、`on_trade_tick`、`subscribe_quote_ticks`、`LoggingConfig`
    - v2：`LiveNode`、`LiveNodeConfig`、`DataActorConfig`、`LoggerConfig`、`subscribe_quotes`、`def on_quote`
- PyPI（`--offline` 時略過；逾時 5 秒）：讀 `https://pypi.org/pypi/nautilus_trader/json`，取 `stable`、`prerelease`，算出 `pre_flag_required`。2.0.0 正式版發布後這個值會自動變 false，skill 不必改。測試可用 env `NAUTILUS_AGENT_PYPI_URL` 注入 fixture。
- 版號對應 docs ref：
  - 確切版本 `1.231.0` 對到 `v1.231.0`；`2.0.0rc5` 對到 `v2.0.0rc5`。
  - `.devYYYYMMDD` 對到 `develop`，並標註 unreleased。
  - 只知道 generation 時：v1 用 PyPI 最新 1.x tag，查不到就用 `develop_v1`；v2 用最新 2.x tag，查不到就用 `develop`。
  - 若是範圍 pin，標 `approximate`。
- 輸出：`{python, python_version, package:{installed, importable, version, generation, native_core, origin, import_error}, project_evidence:{pins[], crates[], markers:{v1[], v2[]}, heuristic, scan_truncated}, pypi:{status, stable, prerelease, pre_flag_required}, recommendation:{generation, version, docs_ref, approximate, reason, conflicts[]}, cache_root, cached_refs[]}`

**`docs (--ref REF | --project P [--python PY]) [--refresh] [--offline] [--dry-run] [--cache-dir D]`**
- 抓取方式：`git clone --depth 1 --filter=blob:none --no-checkout --branch <ref> https://github.com/nautechsystems/nautilus_trader.git`，接著 `git sparse-checkout set --no-cone '/docs/**/*.md' '/examples/' '/MIGRATION_V2.md' '/RELEASES.md' '/ADAPTERS.md' '/ROADMAP.md'`，再 checkout。
  - 只需要 git，不需要 gh 或 token，也不受 API rate limit 影響。
  - 實測大小：docs 的 md 約 2.5–2.9MB；examples 在 rc5 約 446KB、1.231.0 約 830KB。檔案夠小，examples 預設就一起抓。
  - `.git` 不保留，只留下檔案內容。
- 快取：
  - 位置：`<cache_root>/refs/<sanitized-ref>/{manifest.json, .lock, generations/<uuid>/…}`；manifest 記錄 `ref`、`commit`、`checked_at`、`files`、`root_files_present`。
  - Tag 視為不可變：有 cache 就回 `cached`，不連網。加 `--refresh` 會用 `git ls-remote` 核對 commit，判定 `unchanged` 或 `updated`。
  - Branch 的 TTL 是 24h，過期後用 `ls-remote` 判定 `unchanged` 或 `updated`。
  - 失敗處理：網路失敗但有 cache 回 `stale`（exit 0）；沒有 cache 則 exit 3。`--offline` 只用 cache，沒有 cache 就 exit 2。ref 不存在時 exit 2，並列出最接近的 tags。
- 不做 `index.jsonl`：來源本身就是 repo 的 markdown，`rg` 直接給出原始行號。
- 輸出：`{status, ref, commit, root, docs_dir, examples_dir, root_files{}, files, checked_at, [warning]}`

### 5. Tests `tests/test_nautilus_trader.py`

unittest，全程離線。把 `FAKE_GIT` 放在 PATH 最前面：clone 時產生假的 docs/examples 樹，`ls-remote` 的結果由 env 控制，也能由 env 觸發失敗。

- **Environment**
  - XDG 優先序（含相對路徑、含空白的路徑）。
  - `.venv` 解析。
  - 假 v1 套件與假 v2 套件（帶 `_libnautilus` marker）要辨識出正確的 generation 與 `native_core`。
  - pin 解析：`uv.lock`、`requirements`、pyproject 範圍 pin 要標 approximate，`Cargo.lock` crates 也要讀到。
  - marker 掃描：`DataActorConfig` 不能被當成 v1 的 `ActorConfig`；超過上限要標 truncation。
  - 決策優先序，以及 conflicts 的回報。
  - 版號對應 ref：`1.231.0`、`2.0.0rc5`、`.dev`、只知道 generation 的 fallback。
  - PyPI fixture：stable 1.x 加 pre 2.x 時 `pre_flag_required` 為 true；stable 2.0.0 時為 false；`--offline` 時為 `skipped`。
- **Docs**
  - 首次同步回 `updated`，且 sparse 範圍內的檔案正確。
  - Tag 第二次同步回 `cached`，不呼叫 git。
  - Branch 過了 TTL：commit 相同回 `unchanged`，不同回 `updated`。
  - 失敗情境：有 cache 回 `stale`；沒有 cache 回 exit 3；`--offline` 缺 cache 回 exit 2。
  - `--dry-run` 不寫檔，且 CLI stdout 是合法 JSON（subprocess）。
  - lock 競爭。
  - 缺少的 root 檔要記在 manifest。
- **Marketplace**：`./local/nautilus-trader` 在 `quantitative-finance` 裡。

### 6. Repo 整合

| 檔案 | 變更 |
|---|---|
| `skills/.claude-plugin/marketplace.json` L64-75 | `quantitative-finance.skills` 加入 `./local/nautilus-trader`；description 補上「event-driven backtesting to paper/live trading with NautilusTrader」；tags 加 `nautilus-trader`、`live-trading` |
| `skills/local/vectorbt/tests/test_vectorbt.py` L322 | 把 `nautilus-trader` 加進 `expected` |
| `skills/local/vectorbt/SKILL.md` L10-11 | 加一句分流：事件驅動回測、paper/live 交給 `nautilus-trader` |
| `Makefile` L1, L106-108 | `.PHONY` 與新 target `test-nautilus-trader-skill` |
| `.github/workflows/validate.yml` L83-84 後 | 新增 step "Test NautilusTrader skill helpers" |
| `docs/skills/nautilus-trader.md` + `.zh-TW.md` | 仿 vectorbt 頁：What ships / Quick start / Generations / XDG and freshness / Live-trading gates / Validation baseline / Sources |
| `docs/skills/index.md` L23 後、`index.zh-TW.md` L26 後 | 新增一列 |
| `mkdocs.yml` L118 後 | `- nautilus-trader: skills/nautilus-trader.md` |
| `README.md` L78-79、L84 附近 | 群組說明那句 + local bullet |
| `docs/catalog/domains/quant-research.md` + zh-TW | Local 表加一列；External skills 表加兩個社群 skill（`skipped`：無 license / v1-only）；刪除 L41（zh-TW L46）的 Nautilus backlog bullet |
| `TODO.md` | `./scripts/promote-todo.sh --title "Nautilus Trader skill" --summary "…"` |

pitfall 檔不預先寫：pitfalls 應該來自真實的 debug 紀錄；實作途中若真的踩到雷再補。沒有明確要求就不 commit。

## Verification

1. `make test-nautilus-trader-skill` 與 `make test-vectorbt-skill` 全綠。
2. `bash skills/local/skill-author/scripts/lint-skill.sh skills/local/nautilus-trader` 沒有 error；`make validate`（frontmatter、marketplace、TODO 格式）通過。
3. `make native-marketplace-smoke`：`quantitative-finance` 群組現在有 3 個 skill，Claude 與 Codex 的 smoke 都要過。
4. `uv sync --extra docs && make docs-build`（strict build，含 zh-TW）。
5. 真實網路 smoke，在 scratchpad 進行：
   - `nt_context.py docs --ref v1.231.0` 與 `--ref v2.0.0rc5` 都回 `updated`；再跑一次回 `cached`。
   - 在 v2 cache 用 `rg -l TradingNode` 確認 marker 的前提。
   - 開兩個獨立 uv venv（Python 3.12）：一個裝 `nautilus_trader==1.231.0`，一個裝 `--pre nautilus_trader==2.0.0rc5`。對兩個 venv 各跑 `doctor --python`，要辨識出正確的 generation、`native_core` 與 `docs_ref`，並回報 `pre_flag_required: true`。
   - 在 v2 venv 的全新 process 裡，跑 cache 中一個不需要外部資料的官方 backtest example，並產生 fills report。
