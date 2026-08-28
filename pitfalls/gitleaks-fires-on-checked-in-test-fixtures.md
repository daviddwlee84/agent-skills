# A secret scanner fires on `agent-history-hygiene`'s checked-in test fixtures

## Symptom

A secret scan of this repo — or of a downstream repo that installed the skill —
reports credential leaks that all point at the skill's own test corpus:

```
Finding:     ANTHROPIC_API_KEY=sk-ant-api03-aaaa…AA
RuleID:      anthropic-api-key
File:        skills/local/agent-history-hygiene/tests/fixtures/real_anthropic.md
```

Variants of the same non-issue:

- `gitleaks` at the repo root flags `real_anthropic.md`, `real_openai.md`,
  `private_key.md` (`private-key`), and `webhook_urls.md`.
- Socket / skills.sh reports "1 alert … Anthropic API key shape."
- A downstream user who ran `bootstrap-project.sh` gets their **freshly-installed
  gitleaks pre-commit hook** blocking a commit, citing the shipped
  `.../agent-history-hygiene/tests/fixtures/*.md`.
- A `/security-review` or GitHub-native secret-scanning pass re-surfaces the
  same set and someone has to re-triage that they're harmless.

## Root cause

The skill's whole job is to detect and redact secrets, so its test suite
**deliberately** ships realistic secret-shape corpora (all-`a` filler, e.g.
`sk-ant-api03-` + 93 chars + `AA`) for the gitleaks rules + `redact_secrets.py`
to fire against. A pattern scanner cannot tell that filler from a real leak, so
it fires — correctly, by design.

The previous mitigation was a repo-root `.gitleaksignore` using `file:rule:line`
fingerprints. Those are fragile: they pin an exact line number (one entry,
`real_openai.md:openai-project-key:9`, had already drifted — the key was on
line 8), depend on the rule ID and the gitleaks scan mode, are honored by
**neither** GitHub-native scanning nor Socket, and **never ship**, so they did
nothing for downstream installs.

## Workaround

Suppress with a marker that travels with the fixture, and let the tests opt back
in when they need firing:

- Append ` <!-- gitleaks:allow -->` (single leading space) after the secret on
  each firing `.md` line.
- **Private-key headers are the exception**: they must not appear as literals at
  all, in fixtures or in `.py` tests, because `detect-private-key` reads no
  marker. Build them at runtime (`pem_header()` in `tests/conftest.py`) or use a
  `__SYNTHETIC_PEM_*__` placeholder. See
  [detect-private-key blocks commits in every repo that installed the skill](detect-private-key-blocks-commits-in-downstream-repos.md).
- The corpus + shell tests **strip the marker before staging** into their
  throwaway repo (`_GITLEAKS_MARKER_RE` in `test_gitleaks_corpus.py`; the `sed`
  in `stage_fixture` in `test_scan_staged.sh`), so the rules still fire and every
  assertion passes.
- For GitHub-native scanning (ignores the marker), exclude the paths in
  `.github/secret_scanning.yml`.
- For Socket / skills.sh (re-derives the shape from content, honors nothing),
  mark the finding as an intentional test corpus — see
  `docs/reference/skills-risk-evaluations.md`.

## Prevention

Invariant: **fake test vectors are out of scan scope by default and only fire
when a test re-plants them.** When adding a firing fixture, always append the
marker, and keep the strip **byte-identical** — never change a secret's length
or the length-sensitive rules (`sk-proj-…{80,}`, `sk-ant-api\d{2}-…{93}AA`, the
webhook regexes) stop matching. `clean.md` / `example_shapes.md` carry no marker
so the strip is a no-op and their must-not-fire assertions hold. Full convention:
the skill's `tests/README.md` "Test-vector hygiene" section. Do **not**
reintroduce a `.gitleaksignore` — its line-pinned fingerprints drift and don't
travel downstream.
