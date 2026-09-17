# Generations, installation and branches

Verified 2026-09-17 against `nautilus_trader` 1.231.0 and 2.0.0rc5. Prefer
`doctor` output (live PyPI metadata) and `RELEASES.md` at the target ref over
the dated facts here.

## Contents

1. [Identify a generation](#identify-a-generation)
2. [Release timeline](#release-timeline)
3. [Install](#install)
4. [Platforms, Python and precision](#platforms-python-and-precision)
5. [Where documentation lives](#where-documentation-lives)

## Identify a generation

| | v1 | v2 |
|---|---|---|
| Versions | `1.x`; 1.231.0 is the final v1 release | `2.0.0rcN` until 2.0.0 is final |
| Core | Cython with some Rust via `core/nautilus_pyo3` | Rust core, PyO3 extension `nautilus_trader._libnautilus` |
| Installed files | `.pyx`/`.pxd` Cython sources | `_libnautilus*` plus generated `.pyi` stubs |
| Config classes | msgspec `Struct` with annotated fields | PyO3 types; custom fields as keyword-only `__init__` args |
| Test helpers | `nautilus_trader.test_kit` | `nautilus_trader.testkit` |
| Live node | `TradingNode` + `TradingNodeConfig` dicts | `LiveNode.builder(...)` |
| Extras | `betfair`, `docker`, `ib`, `polymarket`, `visualization` | `visualization` only |
| Runtime dependencies | declared (pandas and others) | none declared; install what examples use |
| Branch | `develop_v1`: critical security backports for about three months after the v2 cutover | `develop`, merged daily to `nightly`, released as tags |
| Hosted docs | none; use git tags | `latest` (release line) and `nightly` |

Both generations import as `nautilus_trader`. A `vbt`-style alias check is
meaningless here; use the installed version, `native_core`, pins and code.

## Release timeline

| Date | Release |
|---|---|
| 2026-06-29 | 1.230.0 and 2.0.0rc1 (PyPI only) |
| 2026-08-02 | 1.231.0 (final v1) and 2.0.0rc2 |
| 2026-08-21 | 2.0.0rc3 (removed the legacy Cython package) |
| 2026-09-02 | 2.0.0rc4 |
| 2026-09-15 | 2.0.0rc5 (crates 0.64.0) |

Upstream aims for a bi-weekly release schedule. Each release's breaking changes
are listed in `RELEASES.md` at that tag.

## Install

Use a dedicated environment per generation, outside any NautilusTrader source
checkout.

```bash
# v2 (pin the exact version the project targets)
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python --pre "nautilus_trader==2.0.0rc5"
.venv/bin/python -c "import nautilus_trader; print(nautilus_trader.__version__)"  # must start with 2.

# v1 (existing projects)
uv pip install --python .venv/bin/python "nautilus_trader==1.231.0"
```

- Plotly tearsheets: `"nautilus_trader[visualization]"` (with `--pre` for v2).
- Development wheels: `--pre --index-url https://packages.nautechsystems.io/simple`.
  `develop` builds are `.devYYYYMMDD+run` (only the latest is kept); `nightly`
  builds are `.devYYYYMMDD` or `aYYYYMMDD` (30 publication dates kept). Upstream
  does not recommend development wheels or RCs for real-capital live trading.
- Build from source only to change NautilusTrader itself or when no wheel
  exists: rustup, clang (plus lld on Linux), uv, then `make sync` and
  `make build-debug` from a `develop` checkout. The project environment is
  `python/.venv`, and `PYO3_PYTHON` must point at it.
- Docker images: `ghcr.io/nautechsystems/nautilus_trader` and
  `ghcr.io/nautechsystems/jupyterlab`.

## Platforms, Python and precision

- Python 3.12–3.14, following the Scientific Python SPEC 0 window (3.11 was
  dropped in 1.222.0).
- Wheels: Ubuntu 22.04+ (glibc 2.35+) x86_64/ARM64, macOS 15+ ARM64, Windows
  Server 2022+ x86_64. Intel macOS needs a source build, Docker, or Linux.
- Official Python wheels use high-precision (128-bit, up to 16 decimals) value
  types. Rust crates default to standard 9-digit precision unless the
  `high-precision` feature is enabled. Catalogs written in one precision mode
  need conversion for the other; read "Data migrations" in
  `docs/concepts/data/index.md` at the target ref.

## Where documentation lives

- Any tag or branch: `scripts/nt_context.py docs --ref <ref>`. This is the only
  practical source for v1 and for pinned RCs.
- Hosted v2: `https://nautilustrader.io/docs/latest/` and `/docs/nightly/`.
  Raw pages: `https://nautilustrader.io/docs/md/latest/<path>.md`.
- Python API reference (v2): <https://nautechsystems.github.io/nautilus_docs/python-api-latest/>.
- Some hosted `latest` index pages still mentioned `TradingNode` at the time of
  verification. The rc5 tag's docs and examples contained no `TradingNode`, so
  prefer the tag cache when pages disagree.
