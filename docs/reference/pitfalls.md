# Pitfalls format

A `pitfalls/` directory captures non-obvious traps you've already debugged
once, so the next agent (or future you) can grep the symptom and skip
straight to the fix.

This page documents the format used by
[`project-knowledge-harness`](../skills/project-knowledge-harness.md). Same
shape ships in any project that has run the skill's `init.sh`.

## File layout

```
pitfalls/
├── README.md                              # index + cross-reference table
├── <symptom-slug-1>.md                    # one trap per file
├── <symptom-slug-2>.md
└── …
```

The slug is the **symptom**, not the root cause. You search by what you
see in the error, not by the explanation you eventually learned.

## Single pitfall doc — required sections

Each `pitfalls/<slug>.md` should answer four questions in this order:

1. **Symptom** — the verbatim error text or behavior. Copy-paste, don't
   paraphrase. Paraphrasing kills `grep`.
2. **Root cause** — the underlying mechanism, in one or two paragraphs.
3. **Workaround** — exact steps to recover. Code blocks where applicable.
4. **Prevention** — the invariant that, if applied, would have prevented
   the trap. If the prevention is severe enough (silent corruption,
   cross-machine recurrence), graduate it to a Hard invariant in
   `AGENTS.md` / `CLAUDE.md` and link both ways.

The full template lives at
[`skills/local/project-knowledge-harness/assets/pitfall-doc.md.template`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/project-knowledge-harness/assets/pitfall-doc.md.template).

## Title / slug guidance

Write the title the way the search query would look:

| ✅ Symptom-first | ❌ Root-cause-first |
|---|---|
| `gh-api-404-on-tree-endpoint.md` | `vendor-yaml-branch-handling.md` |
| `npx-skills-empty-after-install.md` | `skills-discovery-depth-fallback.md` |
| `mkdocs-strict-fails-on-relative-md.md` | `mkdocs-link-validation-rules.md` |
| `mkdocs-i18n-llms-files-are-empty.md` | `mkdocs-plugin-lifecycle-collision.md` |

The agent reading the pitfall is asking *"is this what just happened to
me?"* — the title needs to match the question, not the answer.

A current repository example is
[`mkdocs-i18n-llms-files-are-empty.md`](https://github.com/daviddwlee84/agent-skills/blob/main/pitfalls/mkdocs-i18n-llms-files-are-empty.md):
the visible symptom is nearly empty or wrong-locale llms output; the underlying
plugin lifecycle collision belongs inside the document, not in its slug.

## When NOT to use `pitfalls/`

- **Project-specific bugs that are already fixed.** Use `git log` /
  CHANGELOG instead. Pitfalls are for traps that can recur.
- **Onboarding gaps.** That's documentation; put it in `docs/` or the
  README.
- **Generic "things to watch out for" lists.** Without a specific symptom,
  there's nothing to grep, so the pitfall doesn't earn its keep.

## Cross-referencing

`pitfalls/README.md` should keep a small table of pitfalls that live
*outside* the directory — for example, a known trap explained inside a
specific design doc. The table lets future agents grep the symptom
keyword from one place even when the explanation lives elsewhere.
