# `ruff format` rewrites committed chat transcripts

## Symptom

A repo that follows `agent-history-hygiene` (commit `.specstory/history/*.md`
alongside the diff) starts failing its lint job on files nobody edited:

```
--- .specstory/history/2026-08-28_04-26-10Z.md
+++ .specstory/history/2026-08-28_04-26-10Z.md
@@ -53,7 +53,7 @@
 @app.cell
 def _(np, slider):
-    np.array([1,2,3]) + slider.value
+    np.array([1, 2, 3]) + slider.value

3 files would be reformatted, 75 files already formatted
```

The earlier variant of the same class points at the *installed skill* instead:

```
6 files would be reformatted
  .agents/skills/agent-history-hygiene/...
```

## Root cause

Two separate leaks of "not our source" into the formatter's scope.

**Installed skills.** `npx skills add` materialises whole skill directories
into `.agents/skills/` (with `.claude/skills/<name>` symlinked to them). That is
vendored third-party code; a formatter has no business owning its style, and no
skill can be format-clean under every downstream `line-length` and rule set.

**Agent transcripts.** Since **ruff 0.16**, `ruff format` formats Python inside
Markdown fenced code blocks. A chat transcript is full of Python — pasted
snippets, deliberately-wrong examples, marimo cells, output that was never valid
source. Formatting it:

- **falsifies the record.** The transcript is evidence of what was said. A
  transcript whose code no longer matches what the model actually emitted is
  worse than no transcript.
- **never converges.** SpecStory rewrites the same file as the session
  continues, so the formatter re-fires on every commit — the same
  non-converging loop as the redactor's old bare-`PRIVATE KEY` match.

Note the failure is version-gated and therefore ambushes you on upgrade: a repo
pinned to `ruff>=0.15,<0.16` is clean, and goes red the day someone widens that
constraint. Nothing about the version bump hints at markdown.

## Workaround

Exclude agent artifact dirs *and* installed skills from formatters and linters,
not just from secret scanners:

```toml
[tool.ruff]
extend-exclude = [
    ".agents", ".claude", ".codex", ".cursor", ".opencode", ".specify", ".specstory",
]
```

`.claude` matters even when `.agents` is already listed: the same files are
reachable through the `.claude/skills/<name>` symlink, and an exclude that names
only `.agents` misses that path. Keep the list mirroring
`assets/artifact-dirs.txt`, plus the two skill-install roots.

## Prevention

Invariant: **agent artifacts are records, not source.** Anything that rewrites
files in place — formatter, linter autofix, codemod, end-of-file-fixer,
trailing-whitespace — must be scoped past the artifact dirs. The skill's own
`.pre-commit-config.yaml.template` already excludes `^\.specstory/` from
`end-of-file-fixer` and `trailing-whitespace` for exactly this reason; ruff is
the same rule applied to a tool the template does not install.

The one deliberate exception is `redact-agent-secrets`, which rewrites
transcripts on purpose — and only ever replaces a secret with a sentinel that
cannot re-match, so it converges in one pass.

Related: [detect-private-key blocks commits in every repo that installed the
skill](detect-private-key-blocks-commits-in-downstream-repos.md) — same shape
(we ship files into the consumer's tool scope), different tool.
