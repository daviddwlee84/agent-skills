# Rust crates

Verified 2026-09-17 against crates 0.64.0 (published with Python 2.0.0rc5).
Upstream warns that the Rust API is under active development and method
signatures and trait requirements may change between releases, so confirm
every signature against the crate version the project resolves.

## Contents

1. [When Rust applies](#when-rust-applies)
2. [Versions and pairing](#versions-and-pairing)
3. [Project setup](#project-setup)
4. [Docs and examples](#docs-and-examples)
5. [Verify](#verify)

## When Rust applies

- The Python v2 package and the Rust crates run the same Rust engine. Choose
  Rust when the application must run without Python or needs native traits and
  crate-level control; choose Python for composition, analysis and the Python
  ecosystem.
- Upstream's capability matrix lists parity for strategies, actors, engines,
  `BacktestNode`, `LiveNode`, catalog, indicators and all official adapters.
  `Controller` and tearsheets are Python-only. TWAP is the only built-in
  execution algorithm on both paths.
- A v1 Python project's `nautilus_trader.core.nautilus_pyo3` imports are v1
  package internals, not the Rust crate API. Pure-Rust work uses the crates
  directly, whichever Python generation a sibling project uses.

## Versions and pairing

- Crates use `0.x` versions unrelated to Python versions: 0.61.0 shipped with
  1.231.0, and 0.64.0 with 2.0.0rc5. To pick a docs ref for crates.io
  dependencies, use the Python release tag published the same day (check
  `RELEASES.md` at candidate tags), or `develop` when tracking git.
- Keep every `nautilus-*` crate on the same version **and** the same source.
  Mixing crates.io and git sources produces type mismatches.
- Cargo snippets in docs can lag one version (rc5 docs still showed `"0.63"`).
  Use the version in `Cargo.lock`.
- MSRV is 1.98.1 and generally tracks the latest stable Rust.
- `nautilus-bitget`, `nautilus-kalshi`, `nautilus-gate` and `nautilus-zerodha`
  exist on crates.io only as 0.0.0 placeholders; they are not adapters.
- License: LGPL-3.0-only from 0.62. Flag distribution obligations when the user
  ships binaries; do not give legal conclusions.

## Project setup

```toml
[dependencies]
nautilus-backtest = "0.64"
nautilus-common = "0.64"
nautilus-execution = "0.64"
nautilus-model = { version = "0.64", features = ["test-support"] }
nautilus-trading = { version = "0.64", features = ["examples"] }
# live trading: nautilus-live plus the venue crate, e.g. nautilus-okx
```

| Feature | Crate | Effect |
|---|---|---|
| `high-precision` | `nautilus-model` | 16-digit fixed precision (default 9); Python wheels use this mode |
| `test-support` | `nautilus-model` | fixtures, builders, specs |
| `examples` | `nautilus-trading` | `EmaCross`, `GridMarketMaker` |
| `streaming` | `nautilus-backtest` | catalog streaming through `BacktestNode` |
| `defi` | `nautilus-model` | DeFi types; implies `high-precision` |

Python wheels use mimalloc. A Rust binary selects its own allocator; add
`mimalloc` only when matching that setup matters, and measure.

## Docs and examples

Sync the paired ref, then read these files from `docs_dir`:

- `concepts/rust.md` — capability matrix, actors, strategies, handlers
- `how_to/write_rust_actor.md`, `how_to/write_rust_strategy.md`
- `how_to/run_rust_backtest.md`, `how_to/run_rust_live_trading.md`

Source examples live under `crates/trading/src/examples/` upstream. The docs
cache does not include `crates/`, so read them on GitHub at the same ref, or use
`cargo doc --open` for the resolved versions.

## Verify

1. `cargo check` and `cargo clippy` with the project's features.
2. `cargo test` for strategy logic, using `test-support` fixtures.
3. Run a small backtest binary and inspect fills and positions, as for Python.
4. For live code, follow `live-trading.md`: sandbox or testnet first, with the
   same authorization gates.
