# `ruff format` rewrites committed chat transcripts

## Symptom

A repository that keeps `.specstory/history/*.md` with the feature diff starts
failing lint on files nobody intentionally edited:

```text
--- .specstory/history/2026-08-28_04-26-10Z.md
+++ .specstory/history/2026-08-28_04-26-10Z.md
@@ -53,7 +53,7 @@
 @app.cell
 def _(np, slider):
-    np.array([1,2,3]) + slider.value
+    np.array([1, 2, 3]) + slider.value

3 files would be reformatted, 75 files already formatted
```

An earlier variant points at an installed skill instead:

```text
6 files would be reformatted
  .agents/skills/agent-history-hygiene/...
```

Repeated commit attempts may alternate between a formatter modifying the
transcript and SpecStory appending the live session again. The diff never
stabilizes.

## Root cause

Two kinds of records leaked into a generic mutator's source scope.

**Installed skills are archival dependencies.** `npx skills add` materializes
whole skill directories under `.agents/skills/`, and other harness roots may
contain the same installed content or symlinks to it. This is vendored code, not
source owned by the consuming repository's formatter. No skill can satisfy
every downstream line length and autofix policy.

**Agent artifacts are review records.** Since **ruff 0.16**, `ruff format`
formats Python inside Markdown fenced code blocks. Transcripts and plans contain
pasted snippets, intentionally broken examples, output, and historical model
responses. Reformatting them:

- **falsifies the record:** the committed bytes no longer represent what the
  model and tools emitted;
- **races the recorder:** a live SpecStory writer can append while the formatter
  rewrites or while pre-commit restores its temporary patch;
- **does not converge:** each actor can replace the other's working-tree bytes.

This is version-gated: a repository clean on ruff 0.15 can begin rewriting
Markdown as soon as its constraint admits 0.16.

## Workaround

Exclude **all** archival and install roots from every generic formatter, linter
autofix, codemod, and generic pre-commit file fixer:

```toml
[tool.ruff]
extend-exclude = [
    ".agents",
    ".claude",
    ".codex",
    ".cursor",
    ".opencode",
    ".specify",
    ".specstory",
]
```

Apply the same root set to other mutators, including
`end-of-file-fixer` and `trailing-whitespace`. `.claude` remains necessary when
`.agents` is listed because `.claude/skills/<name>` may symlink into the same
installed tree; path-based tools can otherwise reach it through the second
root.

Keep scanners and validation hooks enabled for these files. Exclusion from
mutation is not exclusion from secret detection.

If a live session is already involved, stop retrying the commit. Exit through
the foreground recorder, let the exact post-session sync finish, and use the
parent-authorized finalizer after the writer is quiescent.

## Prevention

Invariant: **agent artifacts and installed skills are records, not generic
source-mutation targets.** Every mutator must exclude:

```text
.agents  .claude  .codex  .cursor  .opencode  .specify  .specstory
```

The sole sanctioned post-recording mutator is the quiescent post-session
finalizer. It atomically prepares the exact selected artifacts, materializes
sanitized bytes, and then validates the prepared index. It never runs while the
recorder is live.

Pre-commit is **validation-only for agent artifacts**. It may inspect the staged
snapshot and fail closed, but it must never redact, format, restore, or otherwise
rewrite an agent artifact. The older exception for a mutating
`redact-agent-secrets` pre-commit hook is obsolete; redaction belongs only to the
post-session finalizer.

Related:

- [Pre-commit restores over live SpecStory writes](pre-commit-restores-over-live-specstory-writes.md)
- [Rebase continue refuses on a clean index with a live transcript](rebase-continue-refuses-on-clean-index-live-transcript.md)
- [detect-private-key blocks commits in every repo that installed the skill](detect-private-key-blocks-commits-in-downstream-repos.md)
