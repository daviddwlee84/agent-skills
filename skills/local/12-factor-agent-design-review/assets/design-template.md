# 12-Factor Agent design: [system or workflow]

## Executive summary

- **Mode:** Design
- **User-visible outcome:**
- **Key constraints:**
- **Highest-risk decision:**

## System boundary

### In scope

### Non-goals

### LLM vs deterministic code

| Decision or action | Owner: LLM / code / human | Why | Validation or policy |
|---|---|---|---|

## Event and execution flow

```text
trigger -> canonical event -> state/context -> model decision
        -> validation/policy -> handler -> persisted result -> next transition
```

Describe launch, pause, resume, timeout, cancellation, and terminal paths.

## Factor decisions

| Factor | Relevance: Required / Recommended / N/A | Design decision | Reason | Acceptance check |
|---|---|---|---|---|

List Factor 13 separately as an appendix extension.

## Public interfaces and state

### Triggers and canonical events

### Model decision/tool schemas

### Durable state and event history

### Human request/response contract

## Failure and recovery policy

| Failure class | Retry/repair behavior | Budget or timeout | Escalation | Persisted evidence |
|---|---|---|---|---|

## Evaluation and observability

- Transition/reducer tests:
- Model behavior evals:
- Replay/restart tests:
- Traces and operator evidence:

## Implementation sequence

1. [Smallest architecture-defining step]
2. [Next dependency]
3. [Verification gate]

## Open risks and assumptions

- **Unverified:**
- **Assumption:**
