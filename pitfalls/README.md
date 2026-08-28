# Pitfalls

Past traps we have already debugged. This is a symptoms-first knowledge base:
when the same failure appears again, grepping the symptom here should land on
the root cause and workaround faster than re-debugging from scratch.

This repo's public install surface lives under [`skills/`](../skills/). Files in
`pitfalls/` are tracked repo metadata for maintainers and agents, not part of
the published skill collection layout.

## Pitfalls vs the rest

| Surface | Time direction | Question it answers | Access pattern |
|---|---|---|---|
| `TODO.md` | Future | "What might we do later?" | Read by priority |
| `backlog/<slug>.md` | Future | "What analysis already happened?" | Follow links from `TODO.md` |
| `pitfalls/<slug>.md` | Past | "Have we seen this symptom before?" | Grep by symptom |
| `CLAUDE.md` / `AGENTS.md` | Present | "What rules must agents follow?" | Read top to bottom |

A pitfall graduates into a hard agent rule when the trap silently corrupts
state, recurs across sessions or machines, or has a workaround that is too easy
to forget. When that happens, keep the pitfall doc as history and link to it
from `CLAUDE.md`.

## When to add a pitfall doc

Add `pitfalls/<slug>.md` when all of the following are true:

- The debugging session took long enough that the context is worth preserving
- The symptom would be hard to rediscover from normal docs or web search alone
- A future maintainer or agent could realistically hit the same problem again

Each pitfall doc should capture the verbatim symptom, root cause, workaround,
and prevention guidance.

## Index

| Slug | Symptom keywords | Status |
|---|---|---|
| [`yq-bad-expression-and-silent-null`](yq-bad-expression-and-silent-null.md) | `bad expression`, yq returns null, ISO date parse, `strenv` vs `env` | active |
| [`symlink-target-relative-to-symlink-not-cwd`](symlink-target-relative-to-symlink-not-cwd.md) | dangling symlink, looks valid in `ls -la`, agent skill not loading | active |
| [`mkdocs-strict-rejects-build-time-generated-links`](mkdocs-strict-rejects-build-time-generated-links.md) | `Aborted with N warnings in strict mode`, `llms.txt` link, raw-markdown URL, `unrecognized_links` config | active |
| [`skills-cli-skips-nested-skills-without-full-depth`](skills-cli-skips-nested-skills-without-full-depth.md) | `npx skills add` reports `No matching skills found`, `skills/local/*` invisible, `--full-depth` flag | superseded (depth-3 now discovered in `skills@1.5.14`) |
| [`skills-update-fails-for-series-nested-skills`](skills-update-fails-for-series-nested-skills.md) | `npx skills update` prints `Failed to update` / `Failed to check for deleted skills` for `vendor/<series>/<name>` depth-4 skills; `.claude/skills` symlinks missing; `update` can't pass `--full-depth` | active |
| [`skills-list-reconciles-existing-project`](skills-list-reconciles-existing-project.md) | `--list` rewrites `skills-lock.json`, deletes/recreates `.agents/skills` symlinks, executable bit changes, `Agent detected — installing non-interactively` | active |
| [`deploy-pages-times-out-polling-status`](deploy-pages-times-out-polling-status.md) | `actions/deploy-pages@v5`, `Current status:` empty, `Timeout reached, aborting!`, GitHub Pages service-side hang | active |
| [`evidence-gitignored-media-cannot-embed-in-pr`](evidence-gitignored-media-cannot-embed-in-pr.md) | broken image in PR comment, `.evidence/` screenshot 404, gitignored media has no public URL, demo-evidence | active |
| [`specstory-timestamp-regex-assumes-seconds`](specstory-timestamp-regex-assumes-seconds.md) | evidence bundle dir contains full chat title, SpecStory `HH-MMZ` no seconds, Claude project slug non-alnum, demo-evidence session id | active |
| [`specstory-sync-1-session-not-found-under-macos-var`](specstory-sync-1-session-not-found-under-macos-var.md) | `1 session not found`, synthetic Claude session, macOS `/var` vs `/private/var`, SpecStory slug, physical cwd | active |
| [`gitleaks-fires-on-checked-in-test-fixtures`](gitleaks-fires-on-checked-in-test-fixtures.md) | gitleaks fires on fixtures, `anthropic-api-key` / `private-key` test corpus, Socket 1 alert, downstream pre-commit hook blocks on shipped fixtures, `.gitleaksignore` fingerprint drift, `gitleaks:allow` marker | active |
| [`rebase-continue-refuses-on-clean-index-live-transcript`](rebase-continue-refuses-on-clean-index-live-transcript.md) | `You must edit all merge conflicts`, `git rebase --continue` loops, `git ls-files -u` empty, `AM` file, `.specstory` live transcript rewritten mid-rebase, checkout "local changes would be overwritten", concurrent git in shared worktree | active |
| [`skill-description-colon-breaks-yaml-frontmatter`](skill-description-colon-breaks-yaml-frontmatter.md) | `npx skills` prints `⚠ Skipped … YAML parse error`, `Nested mappings are not allowed in compact mappings`, `mapping values are not allowed in this context`, skill missing from picker, unquoted `description:` with `": "`, ` #` silently truncates description | active |
| [`detect-private-key-blocks-commits-in-downstream-repos`](detect-private-key-blocks-commits-in-downstream-repos.md) | `detect private key.....Failed`, `Private key found: .agents/skills/...`, downstream repo cannot commit anything, hook honours no `gitleaks:allow` / `.github/secret_scanning.yml`, BLACKLIST plain-substring match, shipped skill tests inside consumer scan scope | active |

## Cross-referenced pitfalls

| Trap | Lives in | Why not here |
|---|---|---|
| (none yet) | | |
