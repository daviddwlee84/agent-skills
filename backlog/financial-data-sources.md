# Financial data sources skill set

**Status**: P?
**Effort**: L
**Related**: `TODO.md` · `README.md` · `vendor.yaml`

## Context

This topic started as a nested subtree in the old `TODO.md` covering a mix of
free and paid data vendors across US, Taiwan, and China markets. It needs to be
handled as one evaluation item first, because the real question is not "which
provider should we write about next?" but "what shape should a reusable market
data skill take in this repo?"

## Investigation

The original idea list bundled these candidates together:

- Yahoo Finance (`yfinance`)
- Alpha Vantage
- Quandl
- FRED
- IEX Cloud
- Polygon.io
- Tiingo
- TWSE
- AKShare
- Wind
- JoinQuant
- Tushare

The list mixes several dimensions that should probably not be decided ad hoc:

- Free vs paid APIs
- Retail-friendly vs institution-oriented products
- US-focused vs Taiwan/China-focused coverage
- Raw market-data access vs research workflows built on top of the data

No code spike has been done yet. The next useful step is to decide the intended
user and coverage model before splitting this into implementation-sized skills.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| One skill per provider | Precise and easy to scope | Duplicates setup and decision logic across providers |
| One workflow-oriented umbrella skill | Captures provider trade-offs in one place | Risks becoming too broad without strong boundaries |
| Tiered approach: umbrella guide plus provider deep-dives | Gives users a decision layer and implementation details | Higher maintenance cost and requires consistent cross-linking |

## Current blocker / open questions

- Which audience matters first: general Python quants, Taiwan/China market users, or broader agent-skill consumers?
- Should this repo optimize for accessible/free providers first, or is paid-data coverage acceptable?
- Do we want a single decision-oriented skill first, or direct provider-specific implementation guides?

## Decision (if any)

2026-04 deferred. Keep this as one research-backed `P?` item until the audience
and grouping strategy are explicit.

## References

- `TODO.md` historical source list under "Financial Data Sources"
- `README.md` "Available Skills" section for how this repo currently presents skill families
