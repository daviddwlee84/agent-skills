---
name: 12-factor-agent-design-review
description: 'Design and evidence-review LLM systems with HumanLayer''s 12-Factor Agents. Use whenever planning or auditing an LLM workflow, agent loop, tool-calling app, framework migration, human approval, or unreliable agent—even without naming the method. Covers LLM/code boundaries, prompts/context, typed tools, durable state, control flow, pause/resume, retries, and replay. Not for Twelve-Factor App deployment, prompt-only edits, model comparisons, generic code review, security-only work, or scaffolding.'
---

# 12-Factor Agent Design and Review

Use the 12-Factor Agents principles as an engineering lens, not a certification
checklist. The goal is to expose reliability decisions, evidence, and tradeoffs
for LLM-powered software while keeping deterministic code in charge wherever it
can decide safely and repeatably.

## Select the mode

- **Design** — the user is planning a new LLM workflow or agentic feature.
- **Review** — code or a design/spec already exists and the user wants findings.
- **Mixed** — review the current system first, then design a target architecture.

If the request is ambiguous, infer the mode from available artifacts. Existing
code or a concrete spec implies Review; a desired outcome with no implementation
implies Design. State the selected mode in the output.

## Scope boundaries

This skill covers application architecture: prompts, context construction,
structured model outputs, deterministic execution, state, control flow,
pause/resume, humans, retries, triggers, and replayability.

It does not replace security threat modeling, model evaluation, observability
instrumentation, performance profiling, or a framework-specific implementation
guide. Surface those as follow-up work when relevant instead of pretending the
factor review completed them.

## Load references deliberately

Read [references/factors.md](references/factors.md) before doing a detailed
Design, Review, or Mixed analysis. It defines the factor intent, useful evidence,
and common misreadings. Factor 13 is an appendix/bonus idea, not one of the
canonical twelve.

Read [references/extensions.md](references/extensions.md) only when one of these
conditions applies:

- deeper code-search or evidence-gate guidance is needed;
- the system has enterprise audit, idempotency, or high-risk side effects;
- the user asks about scaffolding, observability, evals, or failure-mode catalogs;
- comparing this workflow with existing 12-factor-agent skills would help.

## Shared workflow

### 1. Establish the system boundary

Identify:

- the user-visible outcome and explicit non-goals;
- every trigger and the canonical event it becomes;
- decisions that genuinely require language-model judgment;
- deterministic validation, policy, routing, and side effects;
- irreversible or high-impact operations;
- persistence, human response, timeout, retry, and recovery boundaries.

Sketch this path before scoring or designing details:

```text
trigger -> canonical event -> state/context builder -> model decision
        -> schema/policy validation -> deterministic handler
        -> persisted event/state -> response, pause, or next turn
```

### 2. Classify factor relevance

Inspect all twelve factors and the Factor 13 appendix, but do not force every
factor into every system.

- **Required** — omission creates a concrete reliability or safety failure for
  the stated workflow.
- **Recommended** — useful at the expected scale or risk, but not a current
  blocker.
- **N/A** — outside the system boundary; include a one-line reason.

### 3. Separate observation from proposal

For Review and Mixed mode, observed facts need evidence from the supplied
artifacts. Recommendations are proposals and must be labeled as such.

Acceptable evidence includes:

- a repo-relative `file:line` citation;
- an exact config, schema, endpoint, table, or event definition;
- a short excerpt from a supplied design document;
- a captured runtime trace when behavior cannot be proven statically.

If targeted search finds nothing but the inspected scope is incomplete, mark the
factor **Unverified**, not Gap. Absence supports **Gap** only after the relevant
entrypoints, state definitions, model boundary, and handlers were inspected.

### 4. Prioritize by consequence

Use severity independently from factor status:

- **Critical** — unvalidated model output can directly cause destructive,
  financial, security-sensitive, or externally visible effects.
- **High** — failures cannot be bounded, resumed, reproduced, or audited.
- **Medium** — reliability degrades under realistic scale, long context, or
  partial failure.
- **Low** — maintainability or clarity improvement with limited current impact.

Do not prioritize by factor number or count of gaps.

## Design mode

1. Resolve the LLM/code decision boundary before selecting a framework.
2. Define typed model outputs and the deterministic handlers they may request.
3. Define one durable event/state model that can reconstruct a run.
4. Define the owned prompt and context builder inputs; do not prescribe a
   template engine unless the system needs one.
5. Define launch, pause, resume, timeout, cancellation, and human-response paths.
6. Define bounded retry/error compaction and escalation behavior.
7. Define how each important transition will be replayed or evaluated.
8. Write the result using
   [assets/design-template.md](assets/design-template.md).

The design must name concrete interfaces and acceptance checks, but should not
invent provider- or framework-specific code unless the user chose that stack.

## Review mode

1. Locate entrypoints, model calls, prompts/context builders, tool schemas,
   handlers, state persistence, retries, human gates, and tests. Prefer `rg` and
   inspect the cited files rather than relying on keyword counts.
2. Pass the scan gate: every in-scope factor has either a path to inspect or a
   note describing the targeted search that found no candidate.
3. Pass the evidence gate before assigning a status:
   - **Strong** — the principle is implemented coherently for the stated risk.
   - **Partial** — useful implementation exists with a material limitation.
   - **Gap** — sufficient evidence shows a missing or unsafe capability.
   - **N/A** — not relevant, with a reason.
   - **Unverified** — artifacts are insufficient for a defensible judgment.
4. Connect each material finding to a user-visible failure mode.
5. Recommend the smallest architectural change that closes the risk; do not
   default to framework removal or a rewrite.
6. Write the result using
   [assets/review-template.md](assets/review-template.md).

## Mixed mode

Complete Review mode first. Preserve confirmed strengths and constraints, then
use Design mode to describe the target state. Every target-state change should
trace back to a review finding, requirement, or explicit future capability.

## Validation loop

Before delivering the artifact:

1. Check that every verdict has evidence or is marked Unverified.
2. Check that every N/A has a reason.
3. Check that recommendations are not written as observed facts.
4. Check that high-risk side effects have validation, policy/idempotency, and a
   human gate when required.
5. Check that retries and loops have termination/escalation behavior.
6. Check that the proposed state can support resume and replay where required.
7. Check that acceptance steps exercise the real model boundary or reducer, not
   only syntax and type checks.

## Gotchas

- **The factors are principles, not a compliance standard.** Do not calculate a
  percentage score or call a system "12-factor compliant."
- **Factor 13 is an appendix.** Label pre-fetching as an extension, never as a
  canonical thirteenth factor.
- **Framework use is not automatically a failure.** The relevant question is
  whether the team can inspect and control prompts, context, state, and flow.
- **Inline prompts are not automatically weak.** Ownership, reviewability,
  versioning, and testability matter more than file placement or Jinja usage.
- **Raw chat messages are not automatically wrong.** Flag them when they are
  unbounded, stale, unfiltered, or impossible to reproduce.
- **"Trigger from anywhere" does not require every channel.** It means execution
  is decoupled from the current UI and can accept the channels the product needs.
- **The 3-10-step guidance is a heuristic.** Domain coherence and context growth
  matter more than a hard method count.
- **Static code cannot prove runtime behavior.** Ask for traces or mark the item
  Unverified when retries, compaction, resume, or model inputs are dynamic.

## Provenance

The canonical methodology is Dexter Horthy / HumanLayer's
[12-Factor Agents](https://github.com/humanlayer/12-factor-agents). This skill's
documentation is an adaptation under CC BY-SA 4.0; see `LICENSE.txt`.
