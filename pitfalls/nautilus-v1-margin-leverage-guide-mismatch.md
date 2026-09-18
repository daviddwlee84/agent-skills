# NautilusTrader v1 reports 10x leverage despite migration guidance saying 1x

Observed on 2026-09-17 during paired output-quality evaluations of the
NautilusTrader skill. Python 3.12.10, `nautilus_trader==1.231.0` and
`nautilus_trader==2.0.0rc5`, in separate environments on macOS ARM64.

## Symptom

The rc5 `MIGRATION_V2.md` says an omitted backtest leverage changed from v1's
1x to v2's 10x. The original v1 fixture omitted `default_leverage`, but inspecting
its initialized margin account produced:

```text
ACTUAL_DEFAULT_LEVERAGE 10
```

Consequently, setting `default_leverage=Decimal(1)` as a supposed compatibility
fix would change this project's original margin assumptions tenfold.

## Cause

The installed 1.231.0 Cython implementation contradicts the general migration
table. Its `nautilus_trader/backtest/engine.pyx:653-657` selects:

```python
if default_leverage is None:
    if account_type == AccountType.MARGIN:
        default_leverage = Decimal(10)
    else:
        default_leverage = Decimal(1)
```

Version-matched official documentation is useful but is not a substitute for
checking the actual installed implementation and account state.

## Verified workaround

Inspect the source project's initialized account **before** engine disposal:

```python
print("ACTUAL_DEFAULT_LEVERAGE", engine.cache.account_for_venue(venue).default_leverage)
```

Preserve that observed value explicitly in the target `add_venue` configuration.
In this fixture, 10x preserved 400 fills, 200 closed positions, and a final
USD 997168.31 balance under both versions. Raw reports still differed at a few
cent-level fee and margin rounding boundaries; equal ending equity did not
mean byte-identical economic history.

## Prevention

- Verify source and target defaults independently for the exact release pair.
- Compare initialized account state, fills and intermediate margin reports,
  not only return/PnL or whether a script executes.
- Separate an intentional unleveraged policy change from compatibility work.
- Treat migration tables as change-discovery aids. Resolve conflicts using
  installed source and deterministic runtime tests, and document discrepancies.
- Do not encode an unverified documentation assertion into an eval oracle.
  This evaluation excluded its original 1x assertion symmetrically after the
  independent runtime probe disproved it.

## Sources

- [1.231.0 backtest engine](https://github.com/nautechsystems/nautilus_trader/blob/v1.231.0/nautilus_trader/backtest/engine.pyx)
- [2.0.0rc5 migration guide](https://github.com/nautechsystems/nautilus_trader/blob/v2.0.0rc5/MIGRATION_V2.md)
