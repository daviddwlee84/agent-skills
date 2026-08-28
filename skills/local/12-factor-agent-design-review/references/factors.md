# Factor intent and evidence guide

Source: [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) by
Dexter Horthy / HumanLayer. This reference paraphrases and operationalizes the
methodology for design and review; it does not replace the upstream essays.

## Contents

1. Natural language to tool calls
2. Own your prompts
3. Own your context window
4. Tools are structured outputs
5. Unify execution state and business state
6. Launch, pause, and resume with simple APIs
7. Contact humans with tool calls
8. Own your control flow
9. Compact errors into the context window
10. Small, focused agents
11. Trigger from anywhere
12. Make the agent a stateless reducer
13. Appendix: pre-fetch likely context

## 1. Natural language to tool calls

**Intent:** Use the model where natural-language interpretation is valuable,
then cross into deterministic software through a typed decision boundary.

**Design questions**

- What decisions require semantic judgment rather than ordinary branching?
- What is the smallest discriminated set of intents and payloads?
- What happens when output is invalid, ambiguous, or unsupported?

**Review evidence**

- Model response schemas and parsers.
- Validation before dispatch.
- Tests covering invalid and ambiguous decisions.

**Common misreading:** Every user message does not need to become a tool call.
Use ordinary code when the mapping is already deterministic.

## 2. Own your prompts

**Intent:** Make prompts inspectable, versioned, reviewable, and changeable
without depending on hidden framework defaults.

**Design questions**

- Where is each system/developer instruction assembled?
- Can a run identify the prompt version and inputs it used?
- Can the team test a prompt change against representative cases?

**Review evidence**

- Prompt builders, constants, templates, or provider request construction.
- Version or release linkage in traces/evals.
- Tests or evals for prompt behavior.

**Common misreading:** A separate prompt directory or template engine is not
required. An inline constant can still be owned; a separate file can still hide
unreviewed defaults.

## 3. Own your context window

**Intent:** Deliberately construct what the model sees instead of treating raw
history as an append-only dumping ground.

**Design questions**

- Which state, events, retrieved data, policies, and errors enter each turn?
- What is filtered, summarized, compacted, or fetched again?
- Can the exact rendered context of a failed turn be reproduced?

**Review evidence**

- Context builders/serializers and token or size budgets.
- Selection, compaction, and stale-data rules.
- Logged or replayable rendered model input.

**Common misreading:** Standard chat-message arrays are not inherently wrong.
The failure is uncontrolled, irrelevant, stale, or irreproducible context.

## 4. Tools are structured outputs

**Intent:** Treat a tool request as data proposed by the model. Deterministic
code validates policy and decides whether/how to execute it.

**Design questions**

- Is every model-selected action represented by a schema?
- Which layer validates authorization, policy, idempotency, and invariants?
- Are model decisions separated from side-effecting handlers?

**Review evidence**

- JSON Schema, Zod, Pydantic, dataclasses, tagged unions, or equivalent types.
- Dispatch and policy code after parsing.
- Rejection tests for invalid or unauthorized payloads.

**Common misreading:** Provider-native function calling is an encoding choice,
not proof that validation and execution boundaries are safe.

## 5. Unify execution state and business state

**Intent:** Make the state needed to understand and continue the workflow part
of the durable domain record rather than scattering it across opaque runtime
checkpoints and business tables.

**Design questions**

- What single thread/event history explains both business progress and agent
  progress?
- Where are attempts, approvals, errors, external IDs, and terminal outcomes?
- Can an operator answer "what happened and what happens next" from durable
  state?

**Review evidence**

- State/event schemas and persistence transactions.
- Correlation and idempotency keys.
- Reconstruction/replay code and operational views.

**Common misreading:** "Single state" need not mean one database row. A coherent
event model spanning normalized tables can be unified; duplicated authorities
cannot.

## 6. Launch, pause, and resume with simple APIs

**Intent:** Make long waits, callbacks, humans, and process restarts normal state
transitions rather than blocked in-memory execution.

**Design questions**

- What launches a run, records a pause, and resumes from a new event?
- Can the process stop safely between model decision and side effect?
- How are duplicate resumes, timeouts, cancellation, and stale callbacks handled?

**Review evidence**

- Launch/resume endpoints, queue consumers, or command handlers.
- Persisted pause reason and continuation data.
- Idempotent callback handling and restart tests.

**Common misreading:** A framework checkpoint is insufficient if the business
record cannot explain it or if approval can occur only at coarse boundaries.

## 7. Contact humans with tool calls

**Intent:** Represent clarification, approval, escalation, and review as typed
workflow actions with durable responses.

**Design questions**

- Which decisions require a person, and what information must they receive?
- Is the response correlated, authenticated, persisted, and resumable?
- What happens on rejection, edits, timeout, or no response?

**Review evidence**

- Human-request and human-response event schemas.
- Approval policy and channel adapters.
- Timeout/escalation and replay tests.

**Common misreading:** Adding a Slack/email notification is not enough if the
response bypasses the state machine or cannot safely resume the exact run.

## 8. Own your control flow

**Intent:** Keep routing, termination, retries, and policy visible in software
the team can inspect and change, even when libraries implement primitives.

**Design questions**

- Which branches belong to code, policy, model judgment, or a human?
- Where are stop conditions, retry budgets, and terminal states defined?
- Can framework behavior be inspected, overridden, and tested?

**Review evidence**

- Explicit loop/router/workflow definitions.
- Termination and transition tests.
- Configuration or wrappers that expose framework defaults.

**Common misreading:** Using LangGraph, an SDK, or a workflow engine is not a
violation. Surrendering important behavior to defaults the team cannot observe
or control is the risk.

## 9. Compact errors into the context window

**Intent:** Feed the model a concise, actionable representation of failures so
it can choose a bounded recovery path without drowning in raw traces.

**Design questions**

- Which errors are retryable, correctable by the model, or terminal?
- What compact error contract enters the next context?
- What caps attempts and escalates repeated or unsafe failures?

**Review evidence**

- Error classification/normalization.
- Retry/step budgets, backoff, and escalation.
- Tests for repeated, non-retryable, and malformed-tool failures.

**Common misreading:** A `catch` block or automatic SDK retry is not error
compaction. Raw stack traces are usually too noisy and may expose secrets.

## 10. Small, focused agents

**Intent:** Keep each model-controlled responsibility coherent enough that its
tools, context, and success conditions remain understandable.

**Design questions**

- Does the workflow cross unrelated domains, policies, or tool sets?
- How many dependent model decisions accumulate into one context?
- Can a typed handoff isolate a subproblem without creating needless agents?

**Review evidence**

- Responsibility and tool boundaries.
- Context growth across representative runs.
- Handoff schemas and end-to-end eval cases.

**Common misreading:** Three to ten steps (perhaps up to roughly twenty) is a
heuristic, not a compliance threshold. Splitting a cohesive five-step workflow
into five personas can make reliability worse.

## 11. Trigger from anywhere

**Intent:** Decouple workflow execution from one UI so the product can accept
the channels and events its users actually need.

**Design questions**

- How do HTTP, CLI, cron, queue, chat, email, or webhook inputs normalize into
  canonical events?
- Is identity, tenancy, authorization, and trace metadata preserved?
- Can new adapters be added without rewriting core execution?

**Review evidence**

- Adapter-to-event normalization.
- Shared application entrypoint or command handler.
- Tests showing equivalent behavior across relevant triggers.

**Common misreading:** A product does not need every channel. One channel can be
correct when execution is not structurally coupled to its UI implementation.

## 12. Make the agent a stateless reducer

**Intent:** Make each transition derive from explicit durable state plus a new
event, so execution can resume, replay, test, and move between workers.

**Design questions**

- Can the next decision be represented as `(state, event) -> transition`?
- What data is hidden in globals, closures, process memory, or provider threads?
- Are side effects separated from pure transition decisions and recorded?

**Review evidence**

- Serializable state/event types and reducer-like transition logic.
- Separate effect execution and effect-result events.
- Replay, serialization, and process-restart tests.

**Common misreading:** Functional syntax is not required. A class-based system
can follow this principle if required state is explicit and transitions are
reconstructable.

## 13. Appendix: pre-fetch likely context

**Status:** HumanLayer presents this as an honorable mention/appendix, not one of
the canonical twelve factors.

**Intent:** Deterministically fetch clearly required data before a model turn
when doing so reduces avoidable tool loops and context uncertainty.

**Design questions**

- Which data is predictably needed for almost every decision?
- What freshness, authorization, and size limits apply?
- Would pre-fetching waste latency/tokens or expose unnecessary information?

**Review evidence**

- Pre-model data-loading stage and context budget.
- Caching/freshness and authorization rules.
- Latency/token measurements or eval comparisons.

**Common misreading:** "Fetch everything" is not the goal. Pre-fetch only data
whose expected value exceeds its cost and disclosure risk.
