# nautilus-trader

Write, debug, review and migrate code that uses **NautilusTrader**, in Python
(`nautilus_trader`) or through the `nautilus-*` Rust crates. This local skill
belongs to the `quantitative-finance` marketplace group with
[vectorbt](vectorbt.md) and
[quantatitive-factor-researcher](quantatitive-factor-researcher.md).

NautilusTrader is mid-transition. The legacy Cython core (v1, `1.x`, final
release 1.231.0) and the Rust core with PyO3 bindings (v2, `2.0.0rcN`) both
install and import as `nautilus_trader`, but their Python APIs differ widely.
While 2.0 is a release candidate, `pip install nautilus_trader` without `--pre`
still installs v1, and the hosted `latest` docs describe v2. No v1 docs are
hosted anymore. The skill therefore identifies the generation and exact version
before using any example, then reads documentation from the matching git tag.

VectorBT remains the tool for vectorized signal research and parameter grids.
This skill covers event-driven backtests (order books, fill and latency
models) and the path from the same strategy code to sandbox, testnet and live
nodes, including adapters for venues and data providers.

## What ships

- A short entrypoint plus on-demand references: generations and installation,
  v1 → v2 migration tables, live/sandbox trading, Rust crates, and sources.
- `nt_context.py doctor` inspects the project's interpreter and reports:
  - the installed version and native core (`cython` or `pyo3`);
  - lock and requirement pins, and `nautilus-*` crates;
  - v1-only or v2-only names in code that imports `nautilus_trader`;
  - PyPI stable vs pre-release state;
  - a recommendation with a docs git ref and any conflicts.
- `nt_context.py docs` copies `docs/`, `examples/`, `MIGRATION_V2.md`,
  `RELEASES.md`, `ADAPTERS.md` and `ROADMAP.md` for one tag or branch into an
  XDG cache. It uses a sparse, partial `git clone`, with no GitHub token, API
  quota or embeddings.
- Live-trading gates: real accounts, credentials and non-sandbox orders need
  explicit user authorization; sandbox and testnet come first.
- Offline tests using local git remotes, synthetic packages and PyPI JSON.

Source: [the local skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/nautilus-trader).

## Quick start

Commands are relative to the installed skill directory; they need Python 3.11+
and git on macOS or Linux.

```bash
python3 scripts/nt_context.py doctor --project /path/to/project --python /path/to/env/bin/python
python3 scripts/nt_context.py docs --project /path/to/project --python /path/to/env/bin/python
# Documentation only, for an explicit tag or branch:
python3 scripts/nt_context.py docs --ref v2.0.0rc5
```

Search the returned `docs_dir` and `examples_dir` with `rg`, read the complete
page or example, then confirm signatures in the project's interpreter. The tag
above is an example, not a default.

## Generations

| | v1 | v2 |
|---|---|---|
| Versions | `1.x` (final 1.231.0) | `2.0.0rcN` |
| Core | Cython (`.pyx`/`.pxd` in the wheel) | Rust, `nautilus_trader._libnautilus` |
| Live node | `TradingNode` + config dicts | `LiveNode.builder(...)` |
| Configs | msgspec `Struct` | PyO3 types |
| Branch / docs | `develop_v1`, git tags only | `develop`, hosted `latest`/`nightly` |

The skill preserves existing v1 projects, recommends v2 with an exact pin for new
work, and states RC status explicitly. Upstream does not recommend release
candidates for live trading with real capital.

## XDG and freshness

The cache root is `--cache-dir`, then an absolute
`$XDG_CACHE_HOME/nautilus-trader-agent`, then `~/.cache/nautilus-trader-agent`.
Each ref lives in `refs/<ref>/` with an atomically replaced manifest and
immutable generations. The previous generation is kept for one swap.

- Tags are immutable. Once cached they return `cached` without network until
  `--refresh` compares the peeled remote commit.
- Branches recheck after 24 hours with `git ls-remote`, returning `unchanged` or
  `updated`.
- A failed remote check with valid cache returns `stale` (exit 0), which must be
  reported. `--offline` uses only valid cache, and `--dry-run` writes nothing.
- No background scheduler is installed.

## Validation baseline

Validated on 2026-09-17 on macOS ARM64 with Python 3.12.10:

- `doctor` identified `nautilus_trader` 1.231.0 (`cython`) and 2.0.0rc5
  (`pyo3`) in separate uv environments. It reported `pre_flag_required: true`
  from live PyPI metadata.
- `docs` synced `v1.231.0` (393 files) and `v2.0.0rc5` (353 files) in about 8
  seconds each. A second run returned `cached` in 0.06 seconds.
- The v1/v2 name markers found no v1 names in the rc5 docs and examples. The v1
  tag produced v2 hits only from its `interactive_brokers_v2` preview examples.
- The rc5 quickstart ran in a fresh v2 process with 902 fills and 451 positions.
  The same file under v1 failed with
  `ImportError: cannot import name 'OrderSide' from 'nautilus_trader.model'`.
- A v2 sandbox `LiveNode` built, registered a strategy and disposed without
  credentials. Nothing ran against a venue.

These are tested versions, not dependency pins.

## Sources

- [Documentation](https://nautilustrader.io/docs/latest/), [llms.txt](https://nautilustrader.io/docs/llms.txt) and the [Python API reference](https://nautechsystems.github.io/nautilus_docs/python-api-latest/)
- [Repository](https://github.com/nautechsystems/nautilus_trader), [`MIGRATION_V2.md`](https://github.com/nautechsystems/nautilus_trader/blob/develop/MIGRATION_V2.md) and [releases](https://github.com/nautechsystems/nautilus_trader/releases)
- [PyPI](https://pypi.org/project/nautilus_trader/) and [crates.io](https://crates.io/crates/nautilus-model)
- Community: [Discord](https://discord.gg/NautilusTrader) and [GitHub Discussions](https://github.com/nautechsystems/nautilus_trader/discussions)

The community skills surveyed during authoring had no license, and one targeted
only v1, so this skill is independently authored.
