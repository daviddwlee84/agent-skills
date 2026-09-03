# Skill risk evaluations on skills.sh

[skills.sh](https://skills.sh/daviddwlee84/agent-skills) runs three independent
audits against every skill in this repo and surfaces the verdicts on the catalog
page:

| Auditor | What it checks |
| ------- | -------------- |
| **Gen** (Agent Trust Hub) | High-level "is this skill safe to install?" verdict produced by Gen's own model. |
| **Socket** | Static scan of skill files for credential-shape strings, suspicious install scripts, network calls, obfuscation, etc. |
| **Snyk** | A combination of standard CVE/SCA on declared dependencies plus a set of AI-skill-specific rules (W0xx) targeting prompt-injection / agent-facing risks. |

This page records the **current findings** and the reasoning for each, so a
reader (or future me) does not have to re-derive whether a flag is a real
problem or expected noise.

## Current findings

As of the most recent audit run shown on
[skills.sh/daviddwlee84/agent-skills](https://skills.sh/daviddwlee84/agent-skills):

| Skill | Gen | Socket | Snyk |
| ----- | --- | ------ | ---- |
| `mkdocs-site-bootstrap`     | Safe | 0 alerts | **Med Risk** |
| `project-knowledge-harness` | Safe | 0 alerts | Low Risk |
| `agent-history-hygiene`     | Safe | **1 alert** | Low Risk |

Both flagged items are **expected** and stem from the skills' core
functionality, not from a real vulnerability. The reasoning follows.

## `agent-history-hygiene` — Socket 1 alert (expected)

- **File flagged:** `tests/fixtures/real_anthropic.md`
- **Pattern:** Anthropic API key shape (`sk-ant-api03-aaaa…AA`)
- **Severity:** medium / confidence high

The skill's whole job is to detect and redact secrets in agent transcripts and
plan files. Verifying that `gitleaks` rules + the `redact_secrets.py` substitution
logic actually fire requires a corpus of intentionally-realistic secret-shape
strings. `tests/fixtures/` therefore deliberately contains:

- `real_anthropic.md` — `sk-ant-api03-` followed by 93 filler chars and `AA`,
  which is the exact shape the strict Anthropic rule expects
- `real_openai.md` — `sk-proj-` + 100 chars matching the OpenAI project-key rule
- `private_key.md` — fake `-----BEGIN RSA PRIVATE KEY-----` block

Socket's secret-pattern scanner can't distinguish "all-`a`s placeholder filler
that exists to be matched" from "leaked credential," so it fires on the
fixture. Removing the corpus would silently break the test suite, which
defeats the purpose of having the skill in the first place. The alert stays.

If the alert is annoying on a downstream dashboard, mark it as a false
positive in skills.sh / Socket with the rationale "intentional secret-shape
test corpus for a secret-redaction skill."

### Keeping the fixtures out of scan scope

The fixtures are shaped to trip scanners on purpose, so the standing goal is
"fake test vectors are out of scan scope **by default**, and only fire when a
test re-plants them." How that is enforced across the surfaces that scan this
repo (and downstream installs):

- **gitleaks (this repo, downstream, `npx skills add` copies).** Each firing
  line in the fixtures carries an inline `<!-- gitleaks:allow -->` marker (a
  `# gitleaks:allow` comment for the two PEM headers in
  `test_redact_secrets.py`). The marker travels with the file, so it also
  suppresses in a downstream user's freshly-bootstrapped gitleaks hook. The
  corpus + shell tests strip the marker before staging into their throwaway
  repo, so the rules still fire there. See the skill's
  [`tests/README.md`](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/agent-history-hygiene/tests/README.md)
  "Test-vector hygiene" section for the byte-identical-strip invariant.
- **GitHub-native secret scanning / push protection.** Honors neither the
  marker nor gitleaks config, so the fixtures dir is excluded by path in
  [`.github/secret_scanning.yml`](https://github.com/daviddwlee84/agent-skills/blob/main/.github/secret_scanning.yml).
- **What was removed.** A former repo-root `.gitleaksignore` pinned each finding
  by `file:rule:line`; those fingerprints drift on any line edit (one entry was
  already stale) and never ship downstream. The co-located marker replaces it.

**Socket is a separate scanner that honors none of the above** — it re-derives
the credential shape from file content — so the "mark as false positive"
guidance above still stands for the Socket dashboard specifically.

## `mkdocs-site-bootstrap` — Snyk Med Risk (expected)

This one is **not** a transitive-dependency CVE — pinning, bumping, or
removing a package will not change the score.

- **Rule:** `W011` — Third-party content exposure / indirect prompt injection
- **Risk score:** 0.90
- **Snyk's rationale (verbatim):**
  > The agent will read untrusted, user-generated third-party docs that could
  > contain instructions and thus enable indirect prompt injection.

The skill ships templates that install `mkdocs-llmstxt` and `mkdocs-copy-to-llm`
by default, which produce:

- `/llms.txt` and `/llms-full.txt` — full-content dumps intended for LLM ingestion
- Per-page "copy as markdown for LLM" buttons

On multilingual sites, the managed `scripts/build-docs-site.py` isolates
`mkdocs-llmstxt` from `mkdocs-static-i18n`: root llms files and raw `.md`
sidecars contain the default language only, while translated HTML is built in
a separate strict pass. Direct `mkdocs build --strict` is an HTML-only preview.
This fixes empty/wrong-locale output; it is **not** a trust boundary and does
not sanitize the default-language docs.

Any LLM-driven agent that consumes those endpoints is reading whatever ended
up in `docs/`. If `docs/` accepts external contributions (e.g. open-source
PRs), an attacker can plant prompt-injection payloads in a doc page and have
them flow into a downstream agent's context. Snyk's W0xx ruleset flags that
agent-facing surface.

### Why we accept the score

The whole point of dogfooding `mkdocs-llmstxt` + copy-to-llm is to make these
docs LLM-friendly; degrading that defeats the skill. A real fix is **trust
modeling**, not a dependency change:

- Treat `docs/` as an LLM input boundary (CODEOWNERS on `docs/**`, require
  review for external PRs).
- Document the threat in the skill so downstream users opt in knowingly.

A future opt-out flag on `init-docs-site.sh` (e.g. `--no-llmstxt`) for repos
that don't want the LLM-facing surface is tracked in `TODO.md` rather than
landed pre-emptively.

### See also

- [`reference/mkdocs-2-and-zensical.md`](mkdocs-2-and-zensical.md) — why we
  pin `mkdocs<2` (different rationale, same skill).
- [`reference/docs-stack-recipe.md`](docs-stack-recipe.md) — what the
  bootstrap actually installs.
- [i18n + llmstxt migration guide](https://github.com/daviddwlee84/agent-skills/blob/main/skills/local/mkdocs-site-bootstrap/references/i18n-llmstxt-migration.md)
  — why existing downstream sites need an explicit audit/migration after
  updating the skill.

## Why we don't ship README badges yet

skills.sh **does not currently expose first-party badge endpoints**. We
probed the obvious paths and all returned 404:

```
https://skills.sh/<owner>/<repo>/badge.svg          → 404
https://skills.sh/badge/<owner>/<repo>.svg          → 404
https://skills.sh/api/badge/<owner>/<repo>          → 404
```

That leaves three options if we ever want a row of audit badges in
`README.md`, in increasing order of effort:

1. **Static `shields.io` badges + manual hyperlinks.** Hand-write each
   badge's value (`Safe`, `1 alert`, `Med (W011)`) and link the image to the
   skills.sh detail page. Zero infrastructure, but drifts the moment an
   audit re-runs.
2. **`shields.io` `endpoint` schema + a self-hosted JSON file.** A scheduled
   GitHub Action scrapes skills.sh, writes `badges/{gen,socket,snyk}.json`
   to `gh-pages`, and shields.io's
   [endpoint badge](https://shields.io/badges/endpoint-badge) renders against
   that JSON. Auto-updating, ~half a day to set up.
3. **Vendor-native badges from Snyk / Socket directly.** Snyk and Socket
   each publish their own badges, but they target whole-repo or npm-package
   scopes rather than per-skill verdicts, so they don't represent the same
   thing skills.sh shows.

We've parked all three. Re-evaluate when skills.sh ships a first-party
badge endpoint, or when the audit signal becomes load-bearing for trust
decisions (e.g. external contributors using verdicts to decide whether to
install).

## When to revisit this page

- A new skill lands and gets its first non-trivial audit verdict.
- An existing finding flips (e.g. Socket alert disappears after a Socket
  rule update, or a new W0xx fires).
- skills.sh changes the auditor lineup, or starts publishing badge URLs.
