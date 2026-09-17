# Live, sandbox and paper trading

Written for v2 and verified against 2.0.0rc5 stubs and examples on 2026-09-17.
For v1 `TradingNode` projects, read `docs/concepts/live.md` and the live examples
from the helper's cache at the project's v1 tag instead of this page.

## Contents

1. [Authorization gates](#authorization-gates)
2. [Environments](#environments)
3. [Build and run a node](#build-and-run-a-node)
4. [Operational contracts](#operational-contracts)
5. [Before real capital](#before-real-capital)

## Authorization gates

These actions need explicit user authorization for the specific action, even
when the surrounding task is to build a live system:

- Starting a node in `Environment.LIVE` or against a non-testnet account.
- Reading, creating, or wiring real API credentials.
- Submitting, modifying, or cancelling orders on a real account, including
  "test" orders and `ExecTester` runs.
- Restarting, reconfiguring, or stopping a running production node.

Without that authorization, write the code, run backtests, and run sandbox or
testnet sessions only. Never print, log, or commit credentials; adapter configs
keep them private, and raw config readback is intentionally unavailable.

## Environments

| Environment | Market data | Execution | Use |
|---|---|---|---|
| `Environment.BACKTEST` | historical | simulated venue | research, regression |
| `Environment.SANDBOX` | live venue feed | local simulated matching (`add_simulated_exec_client`) | paper trading without credentials for execution |
| Venue testnet/demo (e.g. `BinanceEnvironment.TESTNET`, `DEMO`) | venue test feed | venue test account | exercising real order flow |
| `Environment.LIVE` | live | real account | production (gated) |

Adapter support differs by venue. Before assuming a capability, read
`docs/integrations/<venue>.md` and `ADAPTERS.md` at the target ref. For example,
the BitMEX adapter was deprecated (last supported in 2.0.0rc6) because the venue
announced a shutdown.

## Build and run a node

Sandbox skeleton adapted from `examples/live/sandbox/exec_tester.py` at
v2.0.0rc5; it built, registered a strategy, and disposed without credentials on
that version. Copy the current example from the cache at your `docs_ref` when
signatures matter.

```python
from nautilus_trader.adapters.binance import BinanceDataClientConfig, BinanceDataClientFactory, BinanceProductType
from nautilus_trader.adapters.sandbox import SandboxExecutionClientConfig, SandboxExecutionClientFactory
from nautilus_trader.common import Environment
from nautilus_trader.live import LiveNode
from nautilus_trader.model import AccountId, Currency, Money, TraderId, Venue

node = (
    LiveNode.builder("PAPER-001", TraderId.from_str("TRADER-001"), Environment.SANDBOX)
    .add_data_client(None, BinanceDataClientFactory(), BinanceDataClientConfig(product_type=BinanceProductType.SPOT))
    .add_simulated_exec_client(
        "BINANCE",
        SandboxExecutionClientFactory(),
        SandboxExecutionClientConfig(
            venue=Venue("BINANCE"),
            starting_balances=[Money(100_000, Currency.from_str("USDT"))],
            account_id=AccountId.from_str("BINANCE-SANDBOX-001"),
        ),
    )
    .build()
)
node.add_strategy(MyStrategy(MyStrategyConfig(...)))
node.run()  # blocks and owns SIGINT/SIGTERM
```

- `run()` blocks on the calling thread. `await node.run_async()` runs on an
  existing asyncio/ASGI loop (single worker, no hot reload); capture
  `node.cache`, `node.portfolio` and `node.handle()` **before** starting it,
  stop with `handle.stop()`, await the task, then call `node.dispose()`.
- Builder options include `with_reconciliation`, `with_risk_engine_config`
  (`LiveRiskEngineConfig`: `max_notional_per_order`, `max_order_submit_rate`,
  `max_order_modify_rate`, `bypass`), cache/message-bus database backing, and
  controllers. Check `LiveNodeBuilder` in the installed stubs for the full set.
- Register components before the node leaves its idle state.

## Operational contracts

- One `LiveNode` or `BacktestNode` per process; runtime state is not isolated.
- Strategy callbacks are synchronous on the event thread. Offload blocking
  I/O, model inference and long calculations to an executor or another process.
- A network failure can leave an order command's outcome unknown. Keep startup
  reconciliation enabled for real accounts, and read
  `docs/concepts/execution/reconciliation.md` for external orders and
  continuous reconciliation.
- Persistence: configure Redis or PostgreSQL through the builder. PostgreSQL
  needs `nautilus database init` and does not persist actor/strategy state.
- Live timeouts are `*_secs` fields on `LiveNodeConfig`.
- Backtest parity does not cover venue rules, transport failures, dispatch
  interleaving, or external activity. Say so when presenting backtest results
  as evidence for live behavior.

## Before real capital

Present this checklist to the user; do not treat it as authorization:

1. Generation and exact version pinned; RC status accepted, or a stable release
   in use.
2. Backtest and sandbox runs reviewed: fills, positions, account reports, and
   rejected or denied orders.
3. Risk engine limits set and not bypassed; startup reconciliation enabled.
4. Credentials come from the environment or a secret store, scoped to trading
   only (no withdrawal permission) where the venue allows it.
5. A stop path is known (`handle.stop()` or a signal) and logs are retained.
6. Testnet order flow exercised for the order types the strategy uses.
