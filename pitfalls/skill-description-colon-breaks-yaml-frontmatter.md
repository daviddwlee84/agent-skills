# `npx skills` skips a skill: "YAML parse error: Nested mappings are not allowed in compact mappings"

## Symptom

`npx skills@latest add daviddwlee84/agent-skills/skills` clones fine, then
quietly drops skills from the picker:

```
⚠ Skipped /var/folders/.../skills/local/fastapi-ai-patterns/SKILL.md — YAML parse error: Nested mappings are not allowed in compact mappings at line 2, column 14:

description: Production patterns and gotchas for building FastAPI services, esp…
             ^

◇  Found 56 skills
```

The install still "succeeds" — the skipped skills simply never appear in the
selection UI, and no non-zero exit code is returned. Three skills were being
dropped this way (`fastapi-ai-patterns`, `fastapi-ai-scaffold`,
`verifiable-surfaces`) before anyone noticed.

The caret points at column 14, i.e. the start of the *value* — misleading,
because the actual offending character is much further right.

## Root cause

An unquoted YAML value (a *plain scalar*) may not contain `": "`. YAML reads
the first colon-space as a key/value separator, i.e. a nested mapping inside a
value that is already a mapping value — which is illegal in flow ("compact")
context:

```yaml
description: Use when you build, review, or debug a FastAPI app: choosing def vs async def
#                                                              ^ second mapping separator → parse error
```

All three broken descriptions used the same natural-English pattern —
`"…, or setting up a model-serving API with the production basics pre-wired: router/service…"`,
`"The invariant: a surface that cannot be exercised…"`. Colon-space is very
easy to write in a long description and there is no visual cue that it breaks
the file.

Why it went unnoticed for so long:

- `skills/local/skill-author/scripts/lint-skill.sh` read frontmatter with a
  permissive `awk` extractor, so the skill "passed" its own lint.
- `make marketplace` only validates that paths exist and contain a `SKILL.md`
  — not that the file parses.
- Claude Code loaded the skills in-repo anyway (via the `.claude/skills/`
  discovery symlinks), so local dogfooding never surfaced the problem. Only a
  real `npx skills add` run does.

## Workaround

Wrap the value in single quotes. Nothing inside a single-quoted YAML scalar is
special except `'` itself (escaped by doubling), so colons, backticks, `#`,
em dashes and slashes are all safe:

```yaml
description: 'Use when you build, review, or debug a FastAPI app: choosing def vs async def…'
```

Rewording to drop the colon works too, but quoting is preferred: it preserves
the exact trigger wording, which is what drives skill selection.

Verify with the same parser the CLI uses (`yaml` on npm):

```bash
make lint-frontmatter                       # yq / PyYAML / js-yaml, whichever exists
./scripts/lint-frontmatter.sh --parser node skills   # exact npx-skills parity
```

## Prevention

- **`make lint-frontmatter`** (→ `skills/local/skill-author/scripts/lint-frontmatter.sh`)
  YAML-parses every `skills/**/SKILL.md`, checks that the root is a mapping with
  string `name` + `description`, and prints an actionable hint naming the file
  line to quote. Run it before publishing, alongside `make marketplace`.
- **`lint-skill.sh` now delegates to it** for the single-skill case, so the
  permissive awk extractor can no longer greenlight a file that real parsers
  reject.
- **Enforced twice**: `.github/workflows/validate.yml` runs the gate on push
  and PR (pinning the npm `yaml` package so CI agrees with the CLI rather than
  with the runner's `yq`), and `make install-hooks` puts the same
  `make validate` in a local `pre-push` hook.
- Other plain-scalar hazards the linter also flags, because they are the same
  class of bug:
  - `description: Do X # not Y` → YAML starts a **comment** at ` #` and
    silently truncates the description. This one *parses*, so it is a warning,
    not an error, and it is the more dangerous variant: the skill installs with
    a quietly shortened trigger string.
  - A value starting with a reserved character (`- ? , [ ] { } # & * ! | > % @ \``).
- Rule of thumb when authoring: **if a description contains `:`, `#`, or starts
  with punctuation, quote the whole value.**

## Where this was hit

Found 2026-07-27 when running
`npx skills add daviddwlee84/agent-skills/skills` and reading the warnings
above the picker. All 62 `skills/**/SKILL.md` files were then swept with both
`yq` and the npm `yaml` package; exactly those three failed, and both parsers
agreed. Fixed by single-quoting the three descriptions; the linter and this
doc were added in the same change.
