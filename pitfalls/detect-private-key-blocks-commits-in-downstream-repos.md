# `detect-private-key` blocks commits in every repo that installed the skill

## Symptom

A downstream project that ran `npx skills add …` for `agent-history-hygiene`
and bootstrapped pre-commit cannot commit *anything* — the failure names the
installed skill's own test files, not the user's work:

```
Auto-redact secrets in agent artifacts...............(no files to check)Skipped
Detect hardcoded secrets.................................................Passed
detect private key.......................................................Failed
- hook id: detect-private-key
- exit code: 1

Private key found: .agents/skills/agent-history-hygiene/tests/test_redact_secrets.py
Private key found: .agents/skills/agent-history-hygiene/tests/README.md
Private key found: .agents/skills/agent-history-hygiene/tests/fixtures/private_key.md
```

Note what passed just above it: gitleaks was **clean**. Only the private-key
hook fires, and it fires on files the user never wrote.

## Root cause

`detect-private-key` (pre-commit/pre-commit-hooks) is not a pattern scanner
with an allowlist. It is ten byte substrings and an `in`:

```python
if any(line in content for line in BLACKLIST):
    private_key_files.append(filename)
```

It therefore honours **no** suppression mechanism that works for the other
scanners in the stack — not an inline `<!-- gitleaks:allow -->` marker, not
`.github/secret_scanning.yml`, not a `.gitleaksignore`. The only two levers are
the consumer's own `exclude:` regex and the bytes on disk.

And the bytes were ours. `npx skills add` materialises the *whole* skill
directory — `tests/`, `fixtures/`, everything — into the consumer's repo at
`.agents/skills/<name>/` (with `.claude/skills/<name>` symlinked to it), which
is squarely inside their scan scope. A skill whose job is *detecting* private
keys naturally had literal key headers in its test corpus, so every consumer
inherited three permanently-failing files with nothing they could add to those
files to stop it.

`assets/redact_secrets.py` had already worked this out for itself — it splits
its OpenVPN token across two adjacent literals with a comment saying exactly
why — but the test suite never got the same treatment.

## Workaround

For a repo stuck on an older installed copy, update the skill
(`npx skills@latest update`). Only as a stopgap, scope the hook past it:

```yaml
      - id: detect-private-key
        exclude: (^|/)agent-history-hygiene/tests/
```

Prefer the location-independent `(^|/)…` form over anchoring at
`^\.(agents|claude)/skills/…`: `npx skills` installs under whichever agent
directory the consumer uses, and that set keeps growing.

## Prevention

Invariant: **no file this repo ships may contain a `detect-private-key`
BLACKLIST substring.** Not tests, not fixtures, not docstrings, not a YAML
comment explaining the hook. Enforced by
`skills/local/agent-history-hygiene/tests/test_shipped_file_hygiene.py`, which
walks the skill root and greps all ten entries — it caught two extra offenders
(its own docstring, and the template comment written to *document* this
pitfall) within minutes of being added.

The three sanctioned ways to need a key header without writing one:

| Where | Mechanism |
|---|---|
| Python tests | `pem_header()` / `pem_block()` / `PUTTY_HEADER` / `OPENVPN_HEADER` from `tests/conftest.py`, assembled at runtime from `"PRIVATE" + " KEY"` |
| Markdown fixtures | `__SYNTHETIC_PEM_BEGIN__` / `__SYNTHETIC_PEM_END__` / `__SYNTHETIC_PEM_HEADER_OPENSSH__`, expanded by the staging helpers via `FIXTURE_PLACEHOLDERS` |
| Prose / comments | Break the substring (`BEGIN <TYPE> PRIVATE KEY`, `PuTTY-User-Key-File-N`, `V<N>`) |

### A clean `.py` is not a clean `.pyc`

The obvious trick — adjacent string literals, `"PuTTY-User-" "Key-File-2"` —
protects the **source and nothing else**. CPython constant-folds it at compile
time, so the intact BLACKLIST entry lands in `tests/__pycache__/*.pyc`. A
downstream user who runs this suite inside their own repo materialises that
directory under `.agents/skills/…/tests/`, and if `__pycache__` is not
gitignored there, the hook fails their commit again — pointing at a build
artifact they never wrote. The same fold put a live
`whsec_` + 32 chars into the bytecode from `"whsec_" + "a" * 32`, which
gitleaks then flagged as `stripe-webhook-secret`.

What actually survives compilation:

- **Split at a digit**, not mid-word: `f"PuTTY-User-Key-File-{n}"`,
  `f"…Static key V{n}"`. The truncated prefix is not itself a BLACKLIST entry,
  and an f-string over a *name* is not folded.
- **Regex character classes**: `redact_secrets.py` matches
  `BEGIN OpenVPN Static key V\d`, which is both fold-proof and better than the
  literal `V1` it replaced.
- **Named lengths**: `"a" * _WHSEC_BODY_LEN` instead of `"a" * 32`.

`test_shipped_file_hygiene.py::TestCompiledBytecodeIsClean` compiles every
module to a temp dir and greps the bytecode, so this is caught at test time
rather than in someone else's repo.

The same file also asserts the redactor scrubs all ten BLACKLIST entries and
that its sentinel does not re-match — a gap there would mean the redact hook
reports a clean pass and `detect-private-key` fails the commit anyway, leaving
the user nothing to fix.

Distinct from
[a secret scanner firing on the test fixtures](gitleaks-fires-on-checked-in-test-fixtures.md):
that one is fixed with markers, because gitleaks reads them. This hook does
not, so markers are not an option and the bytes have to go.
