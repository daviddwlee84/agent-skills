# Conditional extensions and related implementations

Read this reference only when the task needs deeper evidence guidance,
enterprise-risk framing, scaffolding/observability handoff, or comparison with
other 12-Factor Agents skills. The HumanLayer essays remain the canonical source
for the methodology.

## Evidence-first analysis from Beagle

Source:
[`existential-birds/beagle@agent-architecture-analysis`](https://github.com/existential-birds/beagle/tree/main/plugins/beagle-analysis/skills/agent-architecture-analysis)
(Apache-2.0).

Useful extension:

- Require a scan gate before synthesis: every factor needs either a candidate
  artifact or a recorded targeted search with no result.
- Require concrete evidence before assigning a status.
- Keep current implementation, gaps, and proposals in separate fields.

Do not import its rubric literally. The published version is heavily oriented
toward Python, Pydantic, Jinja, REST endpoints, and specific file layouts. Those
are possible implementations, not requirements of the HumanLayer principles.

## Workflow decomposition from tika's skill pack

Source:
[`tika/12-factor-agent-skills`](https://github.com/tika/12-factor-agent-skills)
(documentation CC BY-SA 4.0; code Apache-2.0).

Useful extension:

- Separate design, review, debugging, and scaffolding intents.
- Use explicit design artifacts for prompt, context, tool schema, state, and
  control flow.
- Map reliability symptoms to likely factor boundaries before proposing fixes.

Limitations observed during evaluation:

- Companion skills link to a shared core reference, creating a portability risk
  when a user installs only one skill.
- Its text scanner can scan its own regex/rubric code and report false PASS
  signals when aimed at the repository root.
- The repository was a new, single-commit project when reviewed; use it as design
  input rather than a canonical dependency.

This local skill therefore stays self-contained and does not ship a heuristic
scanner in V1.

## Enterprise and auditability lens

Source: Adnan Masood,
[12 Factor Agents: Framework for Reliable LLM Agents](https://medium.com/@adnanmasood/12-factor-agents-framework-for-reliable-llm-agents-empirical-guidelines-for-scalable-auditable-4b758e0e7979)
(May 24, 2025).

Use this lens when the system has regulated, financial, multi-tenant, or
externally visible effects:

- connect typed decisions to authorization and policy enforcement;
- require durable correlation/idempotency data around side effects;
- preserve enough state and context provenance for audit and replay;
- make convergence, retry budgets, and escalation explicit operational policy;
- distinguish architectural review from empirical model/eval evidence.

This is secondary commentary, not part of the canonical factor definitions.
Link and paraphrase it; do not reproduce paywalled article text.

## Scaffolding, observability, and failure-mode handoff

Source: HumanLayer
[Discussion #61: Collaborators Wanted — create-12-factor-agent](https://github.com/humanlayer/12-factor-agents/discussions/61).

The discussion frames a future `npx`/`uvx` project generator as "shadcn for AI
agents": provide a controllable starting structure without becoming a framework.
Community feedback highlights observability, eval templates, durable state,
failure-mode catalogs, scheduling, cancellation, and human-contact adapters.

When a Design report reaches implementation handoff:

1. Recommend a project template only after prompt/context/tool/state/control-flow
   decisions are explicit.
2. Include trace and eval hooks in the implementation plan, but do not claim
   architecture review proves runtime quality.
3. Include timeout, cancellation, retry, and human-response failure modes.
4. Prefer a small, editable starting point over an abstraction that hides the
   very decisions the methodology says to own.

Scaffolding remains out of scope for this skill. Check the upstream discussion
before recommending or building a separate generator so local work does not
silently duplicate an official tool.
