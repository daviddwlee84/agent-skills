# Publish finalization readiness contract for dev-cli

**Status**: P2
**Effort**: L
**Date**: 2026-09-01
**Related**: `TODO.md` · [`../docs/skills/agent-history-hygiene.md`](../docs/skills/agent-history-hygiene.md) · `/Users/david/Documents/Program/dev-cli/internal/skill/dev-cli/references/agent-retirement.md`

## Context

On 2026-09-01, the post-session lifecycle work in `agent-history-hygiene`
changed the safe Git boundary. A live agent may stage feature work and queue an
inert exact request, but transcript synchronization, sanitation, provenance,
and the ordinary feature-plus-history commit happen only after the recorder
exits. Commit must be proven before rebase, fetch/fast-forward integration,
manual handoff, or checkout removal.

`dev-cli` already has an artifact finalizer and several lifecycle guards, but
its current contract predates that same-commit model. The integration needs a
portable readiness boundary, not a second implementation of recorder or
sanitizer internals.

This document records research only. **Do not implement dev-cli in this
repository.** When implementation starts, update dev-cli's embedded source and
normative docs; an installed user skill is generated/deployed output and is not
authority.

## Current dev-cli behavior

### Existing artifact lifecycle conflicts with the new commit semantics

The current entry points are:

- `/Users/david/Documents/Program/dev-cli/internal/cli/artifact.go`
  - `newPrepareCmd`
  - `newArtifactFinalizeCmd`
  - `scanAgentArtifacts`
  - `ensureArtifactsFinalized`
  - `artifactStatuses`
  - `artifactStatusForPath`
- `/Users/david/Documents/Program/dev-cli/internal/artifact/service.go`
  - `(*Service).Prepare`
  - `(*Service).ObserveSessionEnd`
  - `(*Service).Finalize`
  - `(*Service).finalizeLocked`
  - `(*Service).revalidate`

`(*artifact.Service).Prepare` currently requires product work to be committed,
the index to be empty, and only recognized artifact dirt to remain.
`(*artifact.Service).finalizeLocked` later stages the transcript/plans, invokes
`scanAgentArtifacts`, and creates a separate transcript-only commit:

```text
chore: finalize <provider> agent session
```

That model conflicts with the portable lifecycle's invariant that feature diff,
exact transcript, plan, and provenance land in the same commit. It also gives
dev its own redactor invocation and transcript staging/commit implementation,
which would duplicate the new owner.

### The current guard is CLI-local and incomplete

`ensureArtifactsFinalized` is defined in
`/Users/david/Documents/Program/dev-cli/internal/cli/artifact.go`. It scans
legacy intent records for one canonical worktree, reconciles finalized receipts,
and rejects armed/finalizing/failed or unreachable artifact commits.

Because it is a `cli` package helper rather than a domain/service boundary, it
protects only callers that remember to invoke it. Existing partial coverage:

- `/Users/david/Documents/Program/dev-cli/internal/cli/done_flow.go` —
  `runDone` calls it before done/integration planning.
- `/Users/david/Documents/Program/dev-cli/internal/cli/retire.go` — retirement
  command checks it before calling the service.
- `/Users/david/Documents/Program/dev-cli/internal/cli/worktree.go` —
  `newWtRemoveCmd` checks it before `safeRemoveWorktree`.
- `/Users/david/Documents/Program/dev-cli/internal/cli/park.go` — `newParkCmd`
  checks it only on cold worktree removal.
- `/Users/david/Documents/Program/dev-cli/internal/cli/sweep.go` — `suggestFor`
  and `suggestMergedWorktrees` use it on several cold/retire/removal actions.

The domain service remains callable without the guard:

- `/Users/david/Documents/Program/dev-cli/internal/retire/service.go` —
  `(*Service).Retire` / `(*Service).validateTarget` revalidate runtime, Git
  operation, cleanliness, worktree identity, and ancestry, but know nothing
  about portable finalization readiness.

Known mutation paths that currently bypass or only partially inherit the guard:

- `/Users/david/Documents/Program/dev-cli/internal/cli/git.go` —
  `newGitPullRebaseCmd`, `newGitUncommitCmd`, `newGitRecommitCmd`, and
  `newGitAmendAllCmd` call Git transaction functions without an aggregate
  finalization gate.
- `/Users/david/Documents/Program/dev-cli/internal/gitx/transactions.go` —
  `PullRebase`, `Uncommit`, `Recommit`, and `AmendAll` are reusable domain-level
  mutators. `PullRebase` stashes, pulls with rebase, and restores; `AmendAll`
  stages and commits; none consumes portable readiness. `InProgress` correctly
  treats `rebase-merge`, `rebase-apply`, and `sequencer` as active state while
  deliberately excluding stale `REBASE_HEAD`.
- `/Users/david/Documents/Program/dev-cli/internal/cli/repo.go` —
  `newRepoSyncCmd` performs `fetch --prune` directly.
- `/Users/david/Documents/Program/dev-cli/internal/cli/resume.go` —
  `newResumeCmd` fetches before checkout/runtime reconstruction and may switch
  the canonical checkout.
- `/Users/david/Documents/Program/dev-cli/internal/cli/fleet.go` —
  `newFleetSyncCmd`, `prepareFleetSync`, `syncFleetHosts`, and hidden
  `newFleetApplySyncCmd` coordinate source/remote mutations.
- `/Users/david/Documents/Program/dev-cli/internal/fleet/sync.go` — `ApplySync`
  fetches and may fast-forward a checked-out branch. A direct caller bypasses
  CLI-only checks.
- `/Users/david/Documents/Program/dev-cli/internal/cli/done.go` — `fastForward`
  rebases the task worktree, switches the canonical checkout, and performs an
  ff-only merge. It currently relies on `runDone` having guarded earlier.

The missing invariant is broader than "is there a dev artifact intent?": a
portable request can be recording, queued, syncing, prepared, committing,
rotation-blocked, or recovery-blocked without appearing in dev's legacy store.

## Chosen ownership boundary

### Portable `agent-history-hygiene` owns mutation and private state

The portable skill owns, end to end:

- foreground recorder supervision and exact post-exit sync;
- exact session/transcript/plan selection;
- transcript sanitation and materialization;
- atomic artifact staging;
- provenance and complete commit-message composition;
- one ordinary feature-plus-history commit;
- private lifecycle journal, authorization, receipt, reconciliation, and
  no-retry decision.

Dev must **never** parse private lifecycle journals, infer their on-disk layout,
run the redactor, sanitize transcript bytes, compose managed trailers, or retry
an uncertain commit. Manual LazyGit/CLI handoff remains blocked until the
portable owner proves the commit.

### Dev owns aggregation, policy gates, and user-facing inventory

Add `/Users/david/Documents/Program/dev-cli/internal/artifact/readiness.go` with
provider-neutral public types and service methods:

- `FinalizationReadiness` — dev's stable aggregate model, independent of
  Claude/SpecStory-specific journal details;
- `(*Service).FinalizationReadiness` — obtain the portable read-only status and
  merge it with legacy dev artifact intents during migration;
- `(*Service).WithHistoryReady` — acquire the shared mutation lease, re-read
  readiness under that lease, fail closed on blockers, run one supplied domain
  mutation, then release.

`WithHistoryReady` is the service/domain boundary. CLI commands may render its
error or next action, but correctness must not depend on a CLI-local helper.
Existing `ensureArtifactsFinalized` becomes a compatibility adapter during
rollout and is eventually removed.

## Prerequisite portable contract

Dev implementation is blocked until `agent-history-hygiene` publishes two
stable interfaces. These are prerequisites, not dev-owned behavior.

### 1. Read-only aggregate readiness JSON

The portable skill must expose a bounded, read-only command that inspects its
private journals and emits one versioned JSON document. Dev consumes that
output; it never opens the journals itself.

Required semantic shape:

```json
{
  "schema_version": 1,
  "scope": "repository",
  "history_ready": false,
  "state": "blocked",
  "checkouts": [
    {
      "worktree_root": "/absolute/worktree",
      "history_ready": false,
      "state": "recording",
      "blockers": [
        {
          "code": "writer-active",
          "next_action": "exit-agent-session"
        }
      ]
    }
  ]
}
```

Contract requirements:

- top-level and per-checkout `history_ready` are authoritative booleans;
- `schema_version`, `scope`, `state`, blocker `code`, and `next_action` are
  stable machine fields; prose may be additive but is not control flow;
- output contains no transcript, diff, scanner output, base/complete commit
  message, credential fragment, authorization token, or private journal path;
- states distinguish at least ready/no-request, recording, queued, syncing,
  prepared, rotation-required, committing, recovery-required, failed, and
  unknown/unavailable;
- "commit complete" is true only after exact parent/tree/request receipt proof,
  not merely because HEAD changed or a draft exists;
- manual handoff stays blocked for every state except proven ready;
- unknown schema, malformed output, timeout, or probe failure is fail-closed for
  mutations that can disturb shared refs or destroy a checkout;
- the query itself acquires no mutation authority and changes no Git or
  lifecycle state.

The exact executable/subcommand name remains an open publication detail, but
the JSON semantics above are the compatibility contract dev needs.

### 2. Git-common mutation lease

The portable owner and dev must use the same exclusive lease anchored in the
repository's canonical Git common directory. Per-worktree locks are
insufficient for fetch, ref updates, branch deletion, or fleet fast-forward
because linked worktrees share refs and administrative state.

Lease invariants:

1. The portable finalizer holds the lease across its readiness transition,
   sanitation/staging, message preparation, ordinary commit, and receipt
   persistence.
2. `WithHistoryReady` acquires the same lease **before** granting any protected
   dev mutation, then re-runs the readiness probe while holding it. A status
   read before lease acquisition is advisory only.
3. Lease contention returns a stable busy/blocker code; dev waits only under an
   explicit bounded policy and never steals a lease from a live owner.
4. Ownership is crash-recoverable with process identity/nonce metadata and
   safe stale-owner rules. Deleting an unknown live lease is forbidden.
5. The lease carries no secret or transcript content and is opaque to users.
6. Release happens on success, error, cancellation, and panic-safe cleanup.
7. Repository-scope callers hold one lease for the complete multi-step
   transaction, not separately around individual Git commands.

## Scope policy

Readiness scope follows the mutation, not whichever worktree invoked the CLI.

### Repository scope

Inspect **all registered worktrees** sharing the Git common directory before
operations that can mutate shared refs, remote-tracking refs, stash state, or
branch topology. This includes:

- pull/rebase, rebase-based done integration, ff-only base movement;
- fetch/prune in repo sync and resume;
- fleet source preparation, target fetch, and target fast-forward;
- amend, recommit, uncommit/reset, push, and branch deletion where another
  worktree can observe the ref change.

One non-ready checkout blocks the repository mutation. The blocker reports the
checkout and portable next action without exposing private journal data.

### Checkout scope

Retire/removal operations inspect the target checkout's finalization readiness,
then keep the lease across runtime drain, Git revalidation, and removal. This
applies to:

- `(*retire.Service).Retire`;
- `newWtRemoveCmd` / `safeRemoveWorktree`;
- cold `newParkCmd` removal;
- `suggestFor` and `suggestMergedWorktrees` apply paths.

Checkout scope does not weaken existing caller-containment, live-runtime,
dirty-tree, operation-in-progress, ancestry, or worktree-registration checks.
It adds history readiness as another independent prerequisite.

## Rejected duplication

| Option | Verdict | Reason |
|---|---|---|
| Extend `ensureArtifactsFinalized` at every CLI call site | Rejected | Continues a reminder-based CLI policy; direct service/domain callers still bypass it, and it sees only legacy intents. |
| Port the private journal parser and redactor into Go | Rejected | Creates two authorities for schema, secrets, authorization, and no-retry reconciliation; dev would drift from the portable skill and risk leaking private output. |
| Keep dev's transcript-only `chore: finalize …` commit after the feature commit | Rejected | Violates feature-plus-transcript same-commit semantics and keeps the unsafe split lifecycle. |
| Treat a clean index, no legacy intent, or stable transcript mtime as ready | Rejected | None proves recorder exit, exact sync, prepared tree, or commit outcome. |
| Let LazyGit/CLI commit a prepared draft | Rejected | A draft is not authority; duplicate commits are possible when the first outcome is uncertain. |
| Portable readiness + shared lease; dev aggregates and gates domain services | **Chosen** | One owner understands private state and mutation; dev receives a stable provider-neutral policy signal and can enforce it everywhere. |

## Integration points by current path

| Path | Current symbols | Planned change |
|---|---|---|
| `/Users/david/Documents/Program/dev-cli/internal/artifact/readiness.go` (new) | `FinalizationReadiness`, `(*Service).FinalizationReadiness`, `(*Service).WithHistoryReady` | Implement portable probe adapter, legacy-intent aggregation, scope expansion, shared lease, and typed blockers. |
| `/Users/david/Documents/Program/dev-cli/internal/artifact/service.go` | `Service`, `Prepare`, `ObserveSessionEnd`, `Finalize`, `finalizeLocked` | Stop owning new recorder/sanitize/commit flows; retain legacy intent reconciliation only for migration and route new policy through readiness. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/git.go` | `newGitPullRebaseCmd`, `newGitUncommitCmd`, `newGitRecommitCmd`, `newGitAmendAllCmd` | Call gated service operations; do not perform readiness only in Cobra handlers. |
| `/Users/david/Documents/Program/dev-cli/internal/gitx/transactions.go` | `PullRebase`, `Uncommit`, `Recommit`, `AmendAll`, `InProgress` | Wrap exported mutating transactions at the service boundary; retain stale-`REBASE_HEAD` behavior. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/done_flow.go` | `runDone` | Render readiness blockers, but rely on gated integration services rather than `ensureArtifactsFinalized`. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/done.go` | `fastForward`, `deleteMergedBranch` | Repository-scope lease for rebase/switch/ff/ref deletion transaction. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/repo.go` | `newRepoSyncCmd` | Gate fetch/prune across every worktree in the repository. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/resume.go` | `newResumeCmd` | Gate fetch and any canonical-checkout switch before opening/rebuilding runtime state. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/fleet.go` | `newFleetSyncCmd`, `prepareFleetSync`, `syncFleetHosts`, `newFleetApplySyncCmd` | Carry typed readiness failures through local and remote JSON; gate source and target mutations. |
| `/Users/david/Documents/Program/dev-cli/internal/fleet/sync.go` | `ApplySync` | Enforce repository-scope readiness/lease in the reusable target operation, not only the hidden CLI. |
| `/Users/david/Documents/Program/dev-cli/internal/retire/service.go` | `(*Service).Retire`, `(*Service).validateTarget` | Add checkout-scope `WithHistoryReady` around runtime close, revalidation, worktree removal, optional branch deletion, and task deletion. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/worktree.go` | `newWtRemoveCmd` | Render checkout blocker; underlying removal path must already be gated. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/park.go` | `newParkCmd` | Gate WIP commit/push/ref mutation at repository scope and cold removal at checkout scope. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/sweep.go` | `suggestFor`, `suggestMergedWorktrees` | Include portable blockers in suggestions and recheck under lease when applying. |
| `/Users/david/Documents/Program/dev-cli/internal/cli/list.go` | `jsonRow`, `emitJSON`, `retirementBlockers` | Add nested finalization output; keep `Next` as the human-authored task next action. |
| `/Users/david/Documents/Program/dev-cli/internal/inventory/inventory.go` | `Row`, `Collect` | Attach provider-neutral finalization state to task rows through bounded enrichment. |
| `/Users/david/Documents/Program/dev-cli/internal/inventory/repo_context.go` | `RepoCheckout`, `RepoContext`, `CollectRepoContext` | Carry per-checkout readiness and compute repository aggregation over all worktrees. |
| `/Users/david/Documents/Program/dev-cli/internal/tui/model.go` | `Actions`, `repoItem`, `visibleRepoItems` | Load readiness via existing inventory callbacks; no journal parsing in Bubble Tea. |
| `/Users/david/Documents/Program/dev-cli/internal/tui/view.go` | `(*Model).renderDetail` | Show finalization state, blockers, and machine next action in detail without replacing task `next`. |
| `/Users/david/Documents/Program/dev-cli/internal/skill/dev-cli/references/agent-retirement.md` | normative READY → MERGED → RETIRED flow | Replace legacy prepare/separate artifact-commit wording with portable same-commit readiness and scope/lease rules. |

## JSON and TUI presentation

`dev ls --json` is additive and already treats `jsonRow` as a stable contract.
Add a nested object rather than overloading the legacy flat `artifact_status` or
the human-authored `next` field:

```json
{
  "next": "review API naming with maintainer",
  "finalization": {
    "history_ready": false,
    "state": "queued",
    "scope": "checkout",
    "blockers": [
      {
        "code": "commit-not-proven",
        "next_action": "exit-agent-session"
      }
    ]
  }
}
```

Rules:

- `next` remains the user's task-management note and is never synthesized from
  lifecycle state;
- `finalization.next_action` is machine-derived and bounded;
- repository rows aggregate child checkouts, while expanded TUI checkout detail
  shows the specific blocker;
- keep `artifact_status` during a compatibility window, derived from legacy
  intents only and clearly deprecated; new clients use `finalization`;
- TUI detail renders finalization separately from Git, runtime, and human next
  action. It does not offer a manual Commit action while readiness is false.

## Rollout phases

### Phase 0 — publish portable prerequisites

1. Release the versioned read-only aggregate readiness JSON command.
2. Release the Git-common mutation lease protocol and make the portable
   finalizer use it.
3. Add contract tests proving bounded secret-free output, commit-proof states,
   all-worktree aggregation, lease contention, and crash recovery.
4. Pin the dev embedded skill/source expectation to that released contract.

Dev work must not begin by reverse-engineering the current private journal as a
shortcut around Phase 0.

### Phase 1 — add dev adapter and inventory

1. Add `internal/artifact/readiness.go` and typed provider-neutral models.
2. Merge portable readiness with legacy intent state; either source may block,
   and ready requires both to be clear/proven.
3. Add per-checkout and repository aggregation to inventory.
4. Add nested `finalization` to `dev ls --json` and TUI detail while preserving
   legacy fields.

This phase is read-only and can ship before mutation gates if it labels status
as observational and does not claim readiness without the lease-time recheck.

### Phase 2 — gate destructive checkout operations

1. Put `WithHistoryReady` inside retirement/removal domain paths.
2. Cover `Retire`, `safeRemoveWorktree`, cold park, and sweep apply paths.
3. Preserve all existing runtime/caller/dirty/ancestry checks and revalidate
   them while the shared lease is held.

### Phase 3 — gate shared-ref and multi-step Git operations

1. Wrap pull/rebase, done fast-forward, amend/recommit/uncommit, push, fetch,
   resume switching, and branch deletion at repository scope.
2. Gate fleet source preparation and remote `ApplySync`, carrying stable blocker
   codes in fleet JSON.
3. Hold one lease across each complete multi-step transaction and recheck
   readiness after acquisition.

### Phase 4 — retire the duplicated finalizer

1. Stop creating new dev artifact intents for portable lifecycle runs.
2. Keep read-only reconciliation of historical intents until migrated,
   finalized, or explicitly discarded under existing policy.
3. Remove dev's `scanAgentArtifacts` redactor/stager and transcript-only commit
   path once no supported state depends on it.
4. Remove `ensureArtifactsFinalized` after all service/domain paths use the new
   gate.
5. Update the embedded dev-cli skill and
   `internal/skill/dev-cli/references/agent-retirement.md`; do not patch an
   installed user copy as the source of truth.

## Test plan

### Portable contract tests (agent-history-hygiene)

- versioned JSON is deterministic, bounded, UTF-8, and contains none of the
  forbidden transcript/message/scanner/journal/token data;
- each lifecycle state maps to the correct `history_ready`, blocker code, and
  next action;
- `committed` requires exact receipt proof; a changed HEAD, draft, or stale
  `REBASE_HEAD` is insufficient;
- repository aggregation includes canonical and every linked worktree sharing
  the common dir;
- finalizer/dev lease contention serializes mutation; readiness is rechecked
  after acquisition;
- stale-owner recovery cannot steal from a live process and leaves no permanent
  lock after a crash.

### Dev unit and integration tests

Add `internal/artifact/readiness_test.go` and extend current suites:

- `/Users/david/Documents/Program/dev-cli/internal/artifact/artifact_test.go`
- `/Users/david/Documents/Program/dev-cli/internal/gitx/transactions_test.go`
- `/Users/david/Documents/Program/dev-cli/internal/inventory/repo_context_test.go`
- `/Users/david/Documents/Program/dev-cli/internal/cli/tui_internal_test.go`
- `/Users/david/Documents/Program/dev-cli/internal/cli/tui_load_test.go`
- `/Users/david/Documents/Program/dev-cli/internal/tui/tui_test.go`

Required cases:

1. Strictly decode supported schema; fail closed on unknown version, malformed
   JSON, command failure, timeout, duplicate checkout, or path outside the
   target Git common dir.
2. Prove dev never opens a private journal or invokes the redactor; fake the
   published readiness/lease interfaces instead.
3. Legacy armed/finalizing/failed/unreachable intents block even when portable
   readiness says ready; portable blockers block with no legacy intent.
4. Repository scope finds a blocker in a sibling linked worktree for every
   shared-ref operation. Checkout retirement ignores unrelated ready siblings
   but blocks the target.
5. Each bypass listed above performs **zero Git mutation** while blocked:
   `PullRebase`, `Uncommit`, `Recommit`, `AmendAll`, done rebase/ff, repo/resume
   fetch, fleet fetch/ff, park push/WIP, branch delete, retire, and worktree/sweep
   removal.
6. Two concurrent dev mutations and a dev mutation racing the finalizer serialize
   on the same lease; a state change while waiting is caught by the under-lease
   recheck.
7. Lease release occurs on success, error, cancellation, and panic recovery.
8. `dev ls --json` adds `finalization` without renaming existing fields; human
   `next` remains byte-for-byte unchanged.
9. TUI detail shows per-checkout blockers and repository aggregation without a
   commit action or private path.
10. A proven ready state allows the existing operation and preserves all prior
    transaction receipts/recovery behavior.
11. Stale `REBASE_HEAD` alone does not block; `rebase-merge`, `rebase-apply`, or
    `sequencer` does.
12. Fleet serializes stable blocker codes across the hidden remote command and
    never treats a blocked host as a successful sync.

## Decision

**2026-09-01 — choose the portable readiness + Git-common lease boundary.**

`agent-history-hygiene` is the sole authority for recorder lifecycle, private
journals, sanitization, managed message metadata, ordinary commit, and no-retry
reconciliation. Dev adds a provider-neutral `FinalizationReadiness` adapter,
aggregates legacy intent state during migration, and gates service/domain
mutations through `WithHistoryReady`.

Feature-plus-history commit proof comes before rebase or manual handoff. Dev
must not parse private journals, execute the redactor, or create a competing
transcript-only finalization commit.

## Current blocker / open questions

The design boundary is chosen; implementation is blocked on the portable
contract release. Open questions to settle in Phase 0/1:

1. What executable/subcommand name, timeout, and discovery mechanism publish
   the readiness probe and lease operations to embedded dev-cli installations?
2. Which exact state strings and blocker codes are frozen in schema version 1,
   and which fields may be added compatibly?
3. Does lease acquisition use one helper process, an inherited file descriptor,
   or an opaque token checked on release? The semantics above are fixed, but the
   cross-language mechanism still needs a spike on macOS and Linux.
4. What is the safe stale-owner threshold and identity proof across PID reuse,
   suspend/resume, and networked home directories?
5. When the portable skill is absent or too old, which commands fail closed?
   Proposed default: all checkout-destroying/shared-ref mutations fail closed
   only when repository configuration or legacy state indicates managed agent
   history; otherwise report `unmanaged` distinctly from `ready`.
6. How long must legacy dev artifact intents remain readable, and is there a
   one-shot migration that maps finalized receipts without changing history?
7. How should readiness represent a cold/missing checkout with a surviving
   legacy intent or private run state?
8. Can all-worktree repository probing remain fast enough for `dev ls` and the
   TUI without caching a value that becomes unsafe for mutation? Display may
   cache briefly; `WithHistoryReady` must always re-probe under lease.
9. Should pushes be gated when they publish only already-proven commits but a
   sibling checkout is recording? Conservative repository scope says yes until
   the contract can prove the push cannot expose or disturb pending history.
10. How are readiness failures represented across remote fleet versions during
    rolling upgrades, especially when one host supports only legacy intent
    status?

## References

- [`../docs/skills/agent-history-hygiene.md`](../docs/skills/agent-history-hygiene.md)
- [`../pitfalls/pre-commit-restores-over-live-specstory-writes.md`](../pitfalls/pre-commit-restores-over-live-specstory-writes.md)
- [`../pitfalls/rebase-continue-refuses-on-clean-index-live-transcript.md`](../pitfalls/rebase-continue-refuses-on-clean-index-live-transcript.md)
- `/Users/david/Documents/Program/dev-cli/internal/skill/dev-cli/references/agent-retirement.md` — current normative dev lifecycle; update embedded source later
