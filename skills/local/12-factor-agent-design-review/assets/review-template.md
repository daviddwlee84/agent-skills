# 12-Factor Agent review: [system or workflow]

## Executive summary

- **Mode:** Review or Mixed
- **Inspected scope:**
- **Highest risk:**
- **Strongest existing property:**
- **Unverified boundary:**

Do not report a compliance percentage or aggregate score.

## Boundary map

```text
trigger -> canonical event -> state/context -> model decision
        -> validation/policy -> handler -> persisted result -> next transition
```

Name the files/components implementing each known boundary.

## Factor findings

| Factor | Relevance | Status | Evidence | Risk / consequence | Recommendation | Verification |
|---|---|---|---|---|---|---|

Allowed statuses: **Strong**, **Partial**, **Gap**, **N/A**, **Unverified**.
List Factor 13 separately as an appendix extension.

## Priority findings

### Critical

- **[Factor N] Finding** — `file:line` or document excerpt
  - Consequence:
  - Proposed change:
  - Acceptance check:

### High

### Medium / Low

## Strengths to preserve

- **[Factor N] Strength** — evidence and why it matters.

## Remediation sequence

1. [Smallest change that removes the highest consequence]
2. [Dependency-aware next step]
3. [Regression/replay verification]

## Unverified evidence requests

- [Artifact or runtime trace needed, and which judgment it would resolve]

## Target design (Mixed mode only)

For each target-state change, cite the review finding, requirement, or future
capability that justifies it.
