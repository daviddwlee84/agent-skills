# v1 → v2 migration

Condensed from upstream `MIGRATION_V2.md` at v2.0.0rc5 (verified 2026-09-17).
The copy in the helper's cache at the **target** ref is authoritative: sync it
with `scripts/nt_context.py docs --ref <v2 tag>` and read its relevant sections
before editing. The tables below find candidates; they do not replace that file.

## Contents

1. [Before migrating](#before-migrating)
2. [Procedure](#procedure)
3. [Imports and nodes](#imports-and-nodes)
4. [Configs](#configs)
5. [Callbacks, subscriptions and orders](#callbacks-subscriptions-and-orders)
6. [Inspection and backtest results](#inspection-and-backtest-results)
7. [Behavior changes that alter results](#behavior-changes-that-alter-results)
8. [Known limitations](#known-limitations)

## Before migrating

Establish the concrete reason: a requested feature, a v2-only adapter or API,
end of v1 support, or an explicit migration request. Being on v1 is not by
itself a reason to rewrite a working live system. While v2 is a release
candidate, record the user's acceptance of RC status for real-capital use.

## Procedure

1. Create a separate v2 environment; keep the v1 environment runnable for
   comparison. Never install both into one environment.
2. Run `doctor` on the project to list v1 markers with file and line.
3. Port imports, configs, callbacks and node construction using the tables
   below and the target `MIGRATION_V2.md`.
4. Parquet catalogs: back up first. Catalog order events written before
   `activation_price`/`OrderFilled.info` existed must be regenerated or migrated;
   precision or schema changes use the `to-json`/`to-parquet` binaries in
   `crates/persistence` (read "Data migrations" in `docs/concepts/data/index.md`
   at the target ref). Regenerating from source data is often simpler.
5. PostgreSQL-backed live deployments: run `nautilus database init` before
   starting a v2 node, and rename `AGGRESSOR_SIDE` values `BUYER`/`SELLER` to
   `BUY`/`SELL` only if the enum still contains the old values.
6. Run the same backtest in both environments on identical data and compare
   the fills and positions reports and the account report. Explain every
   difference, including those caused by the behavior changes below.
7. Paper trade in `Environment.SANDBOX` before any live cutover.

## Imports and nodes

| v1 | v2 |
|---|---|
| `nautilus_trader.backtest.engine.BacktestEngine` | `nautilus_trader.backtest.BacktestEngine` |
| `nautilus_trader.backtest.node.BacktestNode` | `nautilus_trader.backtest.BacktestNode` |
| `nautilus_trader.live.node.TradingNode` | `nautilus_trader.live.LiveNode` |
| `nautilus_trader.model.enums.OrderSide` | `nautilus_trader.model.OrderSide` |
| `nautilus_trader.model.identifiers.TraderId` | `nautilus_trader.model.TraderId` |
| `nautilus_trader.adapters.<venue>.config` classes | `nautilus_trader.adapters.<venue>` |
| `nautilus_trader.test_kit` | `nautilus_trader.testkit` |
| `TradingNodeConfig.data_clients` / `exec_clients` | `LiveNode.builder(...).add_data_client` / `add_exec_client` / `add_simulated_exec_client` |
| `NautilusKernelConfig.actors` / `strategies` / `exec_algorithms` | `node.add_actor` / `add_strategy` / `add_exec_algorithm` (or `*_from_config`) |
| `LiveNode.start()` + `poll()` (early v2) | `run()` or `await run_async()` |

`BacktestNode`: call `node.build()`, register components with the run config
ID, then `node.run()`. `LiveNode` owns the trader identity; remove `trader_id`
from adapter execution client configs.

## Configs

| v1 | v2 |
|---|---|
| `ActorConfig` | `DataActorConfig` |
| `ExecAlgorithmConfig` | `ExecutionAlgorithmConfig` |
| `ExecEngineConfig` | `ExecutionEngineConfig` |
| `LoggingConfig` | `LoggerConfig` |
| `TradingNodeConfig` | `LiveNodeConfig` |
| `<Venue>ExecClientConfig` | `<Venue>ExecutionClientConfig` |
| `LiveExecEngineConfig` | `LiveExecutionEngineConfig` |
| `timeout_connection` (and other live timeouts) | `timeout_connection_secs`; `timeout_post_stop` → `delay_post_stop_secs` |
| `Importable*ModelConfig`, `MarginModelConfig` | Construct `ProbabilisticFillModel`, `FixedFeeModel`, `StaticLatencyModel`, `StandardMarginModel`… directly |
| `ControllerConfig` | `DataActorConfig` subclass referenced by `ImportableControllerConfig` |

Custom config fields in v2: declare them as keyword-only `__init__` arguments,
accept `**_kwargs`, call `super().__init__()` with no arguments, and do not reuse
base field names:

```python
from nautilus_trader.config import StrategyConfig


class EMACrossConfig(StrategyConfig):
    def __init__(self, *, fast_period: int = 10, slow_period: int = 20, **_kwargs):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
```

This sketch constructed successfully on 2.0.0rc5 (base keywords such as
`order_id_tag` still pass through). Upstream's reference pattern is
`python/tests/strategies/ema_cross.py` at the target ref. Adapter configs also
moved fields (Betfair, Databento, Interactive Brokers): read their sections in
the target `MIGRATION_V2.md` instead of copying v1 fields.

## Callbacks, subscriptions and orders

| v1 | v2 |
|---|---|
| `on_quote_tick` / `on_trade_tick` | `on_quote` / `on_trade` |
| `on_order_book` / `on_order_book_deltas` / `on_order_book_depth` | `on_book` / `on_book_deltas` / `on_book_depth` |
| `subscribe_quote_ticks` / `subscribe_trade_ticks` | `subscribe_quotes` / `subscribe_trades` |
| `subscribe_order_book_deltas` / `subscribe_order_book_depth` | `subscribe_book_deltas` / `subscribe_book_depth10` |
| `request_quote_ticks` / `request_trade_ticks` | `request_quotes` / `request_trades` |
| `cache.quote_tick(s)` / `cache.trade_tick(s)` | `cache.quote(s)` / `cache.trade(s)` |
| `on_historical_data` for built-in types | `on_historical_bars`, `on_historical_quotes`, `on_historical_trades`… (batches) |
| `on_event` | `on_time_event`, `on_order_event`, `on_position_event`, `on_signal` |
| `modify_order(order, …)` / `cancel_order(order, …)` | pass `order.client_order_id` |
| `cancel_orders(orders)` | `cancel_orders(client_order_ids)` |
| `cancel_all_orders()` (instrument and side scope) | strategy-owned orders only; `strategy_only=False` restores v1 scope |
| `OptionChainManager` | `subscribe_option_chain(...)` + `on_option_chain(slice)` |
| `ExecutionAlgorithm.on_order_list(order_list)` | `on_order_list(order_list, orders)` |

`QuoteTick`, `TradeTick` and `register_indicator_for_*_ticks` keep their names.

## Inspection and backtest results

| v1 | v2 |
|---|---|
| `Strategy.id` / `Actor.id` | `strategy_id` / `actor_id` |
| `Order.events`, `Position.events`, `Position.trade_ids` | method calls: `events()`, `trade_ids()` |
| `Component.is_running` and similar | `is_running()` and similar |
| `Portfolio.analyzer` | `statistics()`, `snapshots()`, `register_statistic()` |
| `is_flat()` / `margins_init()` | `is_net_flat()` / `instrument_initial_margins()` |
| `OrderList.orders` | `client_order_ids()` resolved through `cache.order(...)` |
| `AggressorSide.BUYER` / `SELLER` | `AggressorSide.BUY` / `SELL` |
| `OrderSide.NO_ORDER_SIDE` (and other `NO_*`) | `None`; test with `is None` |
| `BacktestNode.get_engine(s)` | `BacktestRunConfig(dispose_on_completion=False)`, then `node.get_engine_cache(config.id)`, `node.generate_fills_report(config.id)` |
| Portfolio statistics receive `pd.Series` | `dict[int, float]` (returns) or `list[float]` (realized PnLs) |
| PyCapsule helpers (`as_pycapsule`, `from_pycapsule`) | pass typed model objects |

## Behavior changes that alter results

- Omitted backtest `default_leverage`: 10x for margin accounts (v1: 1x). Set
  `default_leverage=Decimal(1)` to keep v1 behavior.
- `PortfolioConfig.use_mark_prices` defaults to `true` (v1: `false`).
- Backtest venues no longer accept `settlement_prices`; add `InstrumentClose`
  data with `close_type=InstrumentCloseType.CONTRACT_EXPIRED`.
- `Order.avg_px` and `Order.slippage` are `Decimal`; `to_dict()` returns them as
  strings.
- A fill that flips a position through zero resets the entry price to the
  flipping fill.
- `PortfolioAnalyzer.realized_pnls()` is in ascending event-time order; PnL
  statistics report NaN for runs with no closed trades instead of being absent.
- A raising custom portfolio statistic is logged, not propagated.
- `OrderBook` pickles are not interchangeable between generations.

## Known limitations

- No generic Python networking clients (`nautilus_trader.network.HttpClient`,
  `WebSocketClient`); use adapter clients or the Rust `nautilus-network` crate.
- v1 `LiveDataClient`/`LiveExecutionClient` subclassing has no equivalent yet;
  out-of-tree Python adapters are still planned upstream.
- `BacktestNode` catalog configs do not support v1 data-client factories,
  downloads, custom data or data frames.
- A custom portfolio statistic cannot be registered before a `BacktestNode`
  run; use `BacktestEngine` for that.
- PostgreSQL cache backing does not persist actor/strategy state or heartbeats;
  Redis does.
