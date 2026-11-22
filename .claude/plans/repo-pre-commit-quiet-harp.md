# Scope in-place rewriters past agent artifacts and vendored skills

## Context

In-place rewriting tools — pre-commit's `trailing-whitespace` /
`end-of-file-fixer`, and `ruff format` — currently reach files that this
project does not own: agent transcripts, skills installed by
`npx skills`, and upstream code under `skills/vendor/`. Every such
rewrite is an unrequested code change that pollutes commits and, worse,
never converges.

The invariant already exists in prose. It is written down twice —
`pitfalls/formatter-rewrites-committed-agent-transcripts.md` and
`skills/local/agent-history-hygiene/SKILL.md:255-265` ("Exclude
`.agents`, `.claude`, `.codex`, `.cursor`, `.opencode`, `.specify`,
`.specstory`"). It is enforced essentially nowhere. Measured in this
repo:

| Fact | Evidence |
|---|---|
| `ruff format .` rewrites 116 files | 40 under `skills/vendor/`, 49 under `skills/local/`, 9 under `.agents/skills/` |
| `.agents/skills/**` is git-tracked | 23 entries; `skill-creator`, `find-skills` are real dirs, hashed in `skills-lock.json` |
| `trailing-whitespace` would rewrite npx-managed files | `skill-creator/scripts/{quick_validate,improve_description}.py` contain trailing whitespace |
| `make sync` fights any reformat | `scripts/sync-vendor.sh:206` does `rm -rf "$dest"` then re-downloads upstream bytes |
| This repo has no ruff config and no `.pre-commit-config.yaml` | only `.pre-commit-hooks.yaml`, which it publishes but never consumes |

Two loops make this actively harmful rather than merely untidy:

1. **Vendor churn.** Reformat 40 files under `skills/vendor/` → next
   `make sync` reverts all of them → the weekly `chore/vendor-sync` PR
   fills with unrelated reverts.
2. **Lockfile drift.** Reformat `.agents/skills/**` → `computedHash` in
   `skills-lock.json` no longer matches → `npx skills update` sees drift
   it cannot explain.

### The finding that changes the fix

**`extend-exclude` alone does not work under pre-commit.** Verified:

```
$ ruff format --check .agents/.../utils.py --config 'extend-exclude=[".agents"]'
1 file would be reformatted                     # exclusion IGNORED

$ ruff format --check .agents/.../utils.py --config 'extend-exclude=[".agents"]' \
                                           --config 'force-exclude=true'
warning: No Python files found under the given path(s)    # correctly skipped
```

Ruff ignores `exclude`/`extend-exclude` for paths passed explicitly on
the command line — which is exactly how the `ruff-pre-commit` hook
invokes it. `force-exclude = true` is the load-bearing setting, and the
workaround currently documented in `pitfalls/` omits it. So the existing
advice protects a manual `ruff format .` and silently fails in the setup
people actually run.

Outcome: make the invariant enforced by config in all three places it
applies, and correct the docs that under-specify it.

## The path set

Seven agent dirs, all dot-prefixed, so one compact regex covers them.
Use `(^|/)` rather than `^` so nested occurrences in a monorepo
(`packages/foo/.claude/`) are caught too:

```
(^|/)\.(agents|claude|codex|cursor|opencode|specify|specstory)/
```

`.claude` must be listed even though `.agents` is: `.claude/skills/<name>`
symlinks into `.agents`, so an `.agents`-only exclude still reaches the
same bytes by the other path.

This repo adds `skills/vendor/` to its own copy — upstream-owned, and
restored verbatim by `make sync`.

**Critical: this must stay a per-hook `exclude:`, never a top-level one.**
A top-level `exclude:` in `.pre-commit-config.yaml` would also disable
`redact-agent-secrets` and `gitleaks` on `.specstory/history` and
`.claude/plans` — the precise directories whose whole purpose is to be
scanned for secrets. Only the in-place rewriters get excluded.

---

## Layer 1 — this repo protects itself

**`pyproject.toml`** — add a `[tool.ruff]` section (none exists today):

```toml
[tool.ruff]
# Nothing here rewrites what we do not own. skills/vendor is restored
# verbatim by `make sync` (sync-vendor.sh rm -rf's the dest), and
# .agents/.claude hold npx-installed skills hashed in skills-lock.json.
extend-exclude = [
    ".agents", ".claude", ".codex", ".cursor",
    ".opencode", ".specify", ".specstory",
    "skills/vendor",
]
# Load-bearing: without this, `extend-exclude` is ignored for paths passed
# explicitly on the command line, which is how pre-commit invokes ruff.
force-exclude = true
```

Deliberately **no** `[tool.ruff.lint]` select-set and **no** format gate
in `make validate`. This is a guardrail, not a new standard — adding a
gate would demand reformatting the 49 `skills/local/` files as a side
effect, which is a separate decision.

**New `.pre-commit-config.yaml`** at repo root, dogfooding the published
hook. Base it on
`skills/local/agent-history-hygiene/assets/pre-commit-config.yaml.template`
(after Layer 2 lands), then extend the rewriter excludes with
`|^skills/vendor/`. Pin `rev:` to the current `ahh-v*` tag.

Note in the file that `pre-commit install` is per-clone, and that
`make validate` / the `scripts/git-hooks/pre-push` hook remain the
separate publish gate.

## Layer 2 — agent-history-hygiene ships the rule it documents

**`skills/local/agent-history-hygiene/assets/pre-commit-config.yaml.template`**
— replace the two `exclude: ^\.specstory/` lines (currently lines 55 and
58) so both rewriters cover all seven dirs. Use a YAML anchor so the two
cannot drift apart (anchors resolve at parse time; pre-commit never sees
them):

```yaml
      - id: end-of-file-fixer
        # Agent artifacts are records, not source; skills under .agents/ and
        # .claude/ are vendored code installed by `npx skills`. Rewriting
        # either produces unrequested diffs that never converge.
        # Per-hook on purpose -- a top-level `exclude:` would also switch off
        # redact-agent-secrets and gitleaks on exactly these dirs.
        exclude: &no-rewrite (^|/)\.(agents|claude|codex|cursor|opencode|specify|specstory)/
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
        exclude: *no-rewrite
```

Leave `detect-private-key` unexcluded — it blocks rather than rewrites,
and the template's existing comment block (lines 38-50) already argues
against widening it.

**`SKILL.md:255-265`** — the bullet currently ends "this is that rule
applied to tools the template does not install", which is now stale.
Rewrite it to state that the template covers its own rewriters, and add
the `force-exclude = true` requirement with the ruff snippet.

**`references/pre-commit-redaction-stack.md`** — while here, fix the
drift agent exploration surfaced: lines 118 and 127-132 describe a
fourth "skill test corpus" allowlist and a template exclude that commit
`eb9b8be` removed. `gitleaks.toml.template` has three `[[allowlists]]`,
not four.

**Regression test.** There is currently *zero* test coverage of the
emitted pre-commit config. Add one to
`skills/local/agent-history-hygiene/tests/test_bootstrap_project.py`
(reuse its existing throwaway-repo fixture): run `bootstrap-project.sh`,
parse the produced `.pre-commit-config.yaml`, and assert (a) both
`end-of-file-fixer` and `trailing-whitespace` carry an `exclude`
matching all seven dirs, and (b) no top-level `exclude:` key exists.

## Layer 3 — stop scaffolding the trap into new projects

`python-project-best-practice` currently emits unscoped `ruff format .`
in three templates with no excludes, so every project it creates
reproduces the pitfall.

**`assets/project/pyproject.toml.tmpl`** — extend the existing
`[tool.ruff]` block (line 78) with the same `extend-exclude` (seven dirs;
no `skills/vendor`) and `force-exclude = true`.

**`references/quality-gates.md`** — document the rule next to the
existing "do not also install black" guidance, including why
`force-exclude` is required rather than optional.

**`scripts/audit-python-project.py`** — add an `artifact-dirs-excluded`
check alongside the existing `ruff-configured` / `black-conflict` pair
(lines 213-224), reusing the same `add(name, status, evidence,
remediation)` helper. Warn when `[tool.ruff]` exists but the agent dirs
are unexcluded or `force-exclude` is unset.

`Justfile.tmpl` and `ci.yml.tmpl` need no edits — once
`force-exclude = true` is configured, their `ruff format .` invocations
become safe as written.

## Layer 4 — correct the pitfall record

**`pitfalls/formatter-rewrites-committed-agent-transcripts.md`** — its
workaround block shows `extend-exclude` only. Add `force-exclude = true`
with the two-command verification above, and note that the
`extend-exclude`-only form fails precisely under the ruff pre-commit
hook. Extend the invariant line to name installed skills and vendored
upstream trees, not just transcripts.

**`CLAUDE.md`** — the pitfall has never graduated into a standing rule.
Add a short note under the vendor section: nothing may rewrite
`skills/vendor/` in place, because `make sync` restores it verbatim.

## Optional, cosmetic: `.gitattributes`

A new root `.gitattributes`:

```
skills/vendor/** linguist-vendored
.specstory/** linguist-generated
```

**This enforces nothing** — `linguist-*` affects only GitHub's diff
collapsing and language statistics; no formatter or pre-commit hook
consults it. Worth adding solely to keep vendor-sync PRs reviewable.
Do not treat it as part of the fix.

---

## Verification

1. **The core regression, before and after.** Currently
   `ruff format --check .agents/skills/skill-creator/scripts/utils.py`
   reports `1 file would be reformatted`. After Layer 1 it must report
   `No Python files found under the given path(s)`. Run the same check
   against a `skills/vendor/` file.

2. **Repo-wide count drops to owned code only.** `ruff format --check .`
   currently reports `116 files would be reformatted`. Afterwards the 40
   `skills/vendor/` and 9 `.agents/` files must be gone from that set;
   only `skills/local/` and `docs/` remain (left unformatted by design).

3. **Secret scanning is not collateral damage.** The most important
   negative test. In a throwaway repo, stage a `.specstory/history/*.md`
   containing a fake key and confirm `redact-agent-secrets` and
   `gitleaks` still fire — proving the excludes did not leak upward into
   a top-level `exclude:`.

4. **Rewriters no longer touch installed skills.** In a throwaway repo,
   `pre-commit run trailing-whitespace --all-files` must leave
   `.agents/skills/skill-creator/scripts/quick_validate.py` byte-identical
   (it has trailing whitespace today, so this fails before the change).

5. **Skill tests.** `make test-skill` for the new
   `test_bootstrap_project.py` assertion.

6. **Publish gates unaffected.** `make validate` must still pass —
   `lint-frontmatter`, `validate-marketplace`, `todo-kanban --validate-only`.

7. **Scaffolder.** Generate a project with
   `python-project-best-practice/scripts/new-python-project.py`, confirm
   the emitted `pyproject.toml` carries both settings, and that
   `audit-python-project.py` passes the new check on it and warns on a
   project missing it.

## Bookkeeping

Add a `pitfalls/` cross-reference rather than a new file — this is the
same trap as the existing entry, which needs correcting rather than
duplicating. Record the shipped work with
`./scripts/promote-todo.sh` only if a matching TODO item is added first;
there is no open one today.
