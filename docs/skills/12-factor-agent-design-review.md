# 12-factor-agent-design-review

Design or review production LLM applications using HumanLayer's
[12-Factor Agents](https://github.com/humanlayer/12-factor-agents) as an
evidence-first engineering lens. The skill supports a greenfield **Design**
mode, an evidence-backed **Review** mode, and a **Mixed** mode that reviews the
current system before proposing a target architecture.

It is intentionally not a compliance scorer or project scaffolder.

## Recommended use cases

| Scenario | Mode | Why this skill fits |
|---|---|---|
| Design a new customer-facing LLM workflow | Design | Makes the LLM/code boundary, typed decisions, durable state, pause/resume, retries, and verification explicit before framework choices harden. |
| Production-readiness architecture review | Review | Requires file/line or document evidence for each verdict and connects gaps to user-visible failure modes. |
| Migrate away from framework-owned behavior | Mixed | Preserves working pieces, identifies which prompts/context/state/control-flow decisions are hidden, then defines a controlled target state. |
| Build async or human-in-the-loop workflows | Design or Review | Covers durable approval requests/responses, callbacks, timeouts, cancellation, idempotency, resume, and replay. |
| Investigate an agent that is "stuck at 80%" | Review | Examines systemic boundaries such as context growth, unbounded retries, hidden state, and unvalidated model outputs. |

## Suitable with limitations

- **Incident diagnosis:** use it after reproducing the failure to find the
  architectural cause. It does not replace logs, traces, or runtime debugging.
- **Security-sensitive agents:** it identifies where model output reaches a
  high-risk effect, but a dedicated threat model and security review are still
  required.
- **Model quality problems:** it verifies context, prompt ownership, eval, and
  replay surfaces; it does not benchmark model accuracy by itself.
- **Implementation planning:** it can define interfaces and acceptance checks,
  but framework-specific code generation belongs to a separate implementation
  or scaffold workflow.

## Do not use it for

- ordinary [Twelve-Factor App](https://12factor.net/) deployment/configuration;
- rewriting one prompt when no application architecture is changing;
- comparing model prices, latency, benchmarks, or provider features;
- generic code review of software with no LLM decision boundary;
- generating a runnable starter project or selecting a framework solely from a
  feature checklist.

## What the skill produces

### Design mode

- system boundary and non-goals;
- LLM vs deterministic code vs human decision table;
- trigger/event/context/model/validation/handler/state flow;
- factor relevance and design decisions with acceptance checks;
- typed tool, state, human-response, failure, eval, and observability contracts;
- dependency-aware implementation sequence.

### Review mode

- inspected scope and evidence coverage;
- per-factor `Strong / Partial / Gap / N/A / Unverified` findings;
- consequence-based severity independent of factor number;
- strengths worth preserving;
- smallest remediation sequence and concrete verification steps.

The skill never emits a "12-factor compliance percentage." Factor 13
(pre-fetch context) is always labeled as an appendix extension rather than a
canonical thirteenth factor.

## Example prompts

```text
Design a refund-support agent for FastAPI + Postgres. It starts from email and
Slack, can refund up to $500 automatically, needs human approval above that,
and must resume safely after a worker restart.
```

```text
Review src/agent/ and docs/refund-workflow.md against 12-Factor Agents. Cite
file:line evidence, distinguish gaps from unverified behavior, and prioritize
the smallest production-readiness fixes.
```

```text
Our LangGraph workflow works in demos but loops on tool errors and cannot resume
after approvals. Review the current design first, then propose a target design
without assuming we must remove LangGraph.
```

## Sources and extensions

The canonical factor intent comes from HumanLayer. Conditional references also
record useful ideas and limitations from:

- [`existential-birds/beagle@agent-architecture-analysis`](https://github.com/existential-birds/beagle/tree/main/plugins/beagle-analysis/skills/agent-architecture-analysis)
  — evidence gates, without its Python-specific implementation rubric;
- [`tika/12-factor-agent-skills`](https://github.com/tika/12-factor-agent-skills)
  — workflow decomposition, without its cross-skill dependency and scanner;
- [Adnan Masood's enterprise analysis](https://medium.com/@adnanmasood/12-factor-agents-framework-for-reliable-llm-agents-empirical-guidelines-for-scalable-auditable-4b758e0e7979)
  — auditability and idempotency lens;
- [HumanLayer Discussion #61](https://github.com/humanlayer/12-factor-agents/discussions/61)
  — scaffolding, observability, eval, and failure-mode handoff ideas.

## Canonical SKILL.md

See
[skills/local/12-factor-agent-design-review/SKILL.md](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/12-factor-agent-design-review/SKILL.md)
for the full workflow, gotchas, templates, and conditional reference rules.
