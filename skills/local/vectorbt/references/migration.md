# OSS / PRO comparison and migration

Read this when a feature gap, measured bottleneck or explicit request makes an
edition change relevant. The presence of PRO access alone is not a migration.

## Establish the concrete gap

1. Identify the installed OSS version and the candidate PRO release. If PRO is
   not installed, use its matching release assets to assess availability and
   label runtime claims as unverified until an isolated environment is tested.
2. Map the requirement to actual APIs/configuration in both versions. Check
   whether OSS already supports it before calling it a PRO-only feature.
3. Read official examples and signatures. Avoid a static feature matrix and
   blanket speed claims: both editions evolve, including execution backends.
4. Explain the proposed benefit, affected calls/data contracts, dependencies and
   verification needed. If the current task doesn't authorize an edition change,
   recommend it without silently changing the project's dependencies.

## Execute a requested migration

- Preserve the baseline and project's normal Git/lockfile workflow. Use isolated
  environments for comparisons; don't replace the user's working environment
  merely to evaluate a candidate.
- Adapt data access, indicators, parameter broadcasting, callbacks and result
  accessors according to the verified APIs. Replacing the import line alone is
  not a migration strategy.
- For preserved behavior, compare identical inputs, signal and execution timing,
  grouping, cash sharing, sizing, fees, slippage, orders, trades and equity.
  Explain intended differences for newly enabled features rather than demanding
  false numerical equivalence.
- For performance, use the same data, parameter count, dtype and output workload;
  separate setup/JIT/cold time from repeated warm runs, and record relevant
  backend/thread settings, memory use and environment versions. Choose workload
  sizes that reflect the user's bottleneck.
- Run the migrated saved code in a fresh process and the project's relevant tests.
  Report what improved, what changed semantically and what remains unverified.

If PRO cannot be accessed, determine whether an OSS implementation meets the
requirement and state concrete limitations. Do not invent a missing API, acquire
membership on the user's behalf, or claim a transient network error proves no
PRO access exists.
