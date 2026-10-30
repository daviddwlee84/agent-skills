# GitHub secret scanning lists only fake alerts while a real credential sits in an agent transcript

**Symptoms** (grep this section): Security → Secret scanning shows only
synthetic / `false_positive` alerts · `gitleaks git . --log-opts="--all"`
reports a `rule=generic-api-key` hit that GitHub never listed · a
`secret:` / `password:` / `token:` value inside `.specstory/history/*.md` with
no provider prefix · the agent wrote "without printing any secret" and the next
tool block contains the file's raw head ·
`secret_scanning_non_provider_patterns = disabled`
**First seen**: 2026-10
**Affects**: any repo that commits agent transcripts (SpecStory, Claude/Cursor
plans) and treats GitHub-native secret scanning as its leak detector
**Status**: active — the detection runbook below works today; installing a
commit-time gate in the affected repo is tracked separately

## Symptom

The Security tab shows a handful of open alerts. Every one turns out to be
synthetic (an all-`a` `whsec_…` test vector, a seeded-RNG `tskey-auth-…`).
Dismissing them as false positives feels like the end of the audit.

It is not. A full-history gitleaks pass over the same repo reports hundreds of
occurrences, including a hit like this (value masked, tool-output shape kept):

```text
3  listen: 127.0.0.1:<port>
4  secret: <value>
```

GitHub never listed it. Just above it in the transcript the agent had written
`Let me read the config … (without printing any secret)`, and the very next
block is the Read tool's raw output of that file.

## Root cause

1. **GitHub alerts on provider patterns, and the non-provider toggle was off.**
   A known prefix or shape per provider (`AKIA…`, `whsec_…`, `tskey-…`) is
   reported; a random-looking string after `secret:` has no provider and is
   invisible. `secret_scanning_non_provider_patterns` was `disabled` on the
   repo (`gh api repos/<owner>/<repo> --jq .security_and_analysis`). Turning it
   on is worthwhile, but treat the alert list as a *lower bound*, not an
   inventory.
2. **The leak came in through a tool result, not through prose.** "Without
   printing any secret" is a promise about what the agent *writes*. The Read
   tool prints whatever it reads, and the recorder stores tool output verbatim.
   SpecStory's native redaction recognises token *shapes* (with known gaps); it
   does not know that a YAML key named `secret` holds a credential.
3. **Nothing scanned the commit.** See
   [`global-pre-commit-hook-silently-skips-repos-without-config`](global-pre-commit-hook-silently-skips-repos-without-config.md).

## Workaround / triage

1. **Scan all history and all refs, not just HEAD.** Keep the report private:
   it holds plaintext values.

   ```bash
   umask 077
   gitleaks git . --log-opts="--all" --no-banner \
     --report-format json --report-path "$(mktemp)" --exit-code 0
   ```

   Delete the report when done.
2. **Collapse to unique values.** Dedupe by `(RuleID, sha256(Secret))`. In the
   audit behind this note, 371 occurrences were 132 distinct values.
3. **Classify each value by evidence, never by a hunch.**
   - 40-hex `sourcegraph-access-token`: `git cat-file -e <value>` proves a real
     object in this repo; the rest are upstream SHAs (`vendor.yaml` history,
     `git ls-remote`, `git branch -vv`). See
     [`sourcegraph-access-token-flags-git-commit-shas`](sourcegraph-access-token-flags-git-commit-shas.md).
   - `private-key`: pull out *complete* `BEGIN … END` blocks whose body is pure
     base64 and try `ssh-keygen -y -f` / `openssl pkey`. A span that contains
     prose is not a key. Do **not** judge by length — EC and ed25519 blocks are
     short.
   - JWT: decode header and payload locally. An `iss` of `127.0.0.1:<port>` and
     an `example.com` address is a local dev stack, not production.
   - Documented samples: compare against the scanner's own published examples.
   - Whatever is left: read the surrounding lines with the value masked.
4. **Never test a suspected credential against its provider.** Ask the
   provider's CLI who *owns* it, using your own session (for AWS,
   `aws sts get-access-key-info --access-key-id <id>` returns the owning
   account without authenticating as the leaked key). Also check provenance
   with `git log`: a key committed years before your fork existed is not yours
   to rotate.
5. **A real finding: rotate at the provider first.** Then follow
   [`agent-history-hygiene/references/remediation.md`](../skills/local/agent-history-hygiene/references/remediation.md).
   On a shared `main` the runbook says not to rewrite history: redact HEAD in a
   new commit and push forward.

## Prevention

- Run the hygiene stack in the repo that commits transcripts: config files plus
  a CI job running `gitleaks git` over all refs.
- Enable `secret_scanning_non_provider_patterns` and
  `secret_scanning_validity_checks` where the plan allows; they widen what
  GitHub reports but do not replace your own history scan.
- When an agent must inspect a config that may hold credentials, redact on the
  way out rather than using a raw Read: `yq 'del(.secret)' file.yaml`,
  `grep -v -i -e secret -e token file`, or `sed 's/^\( *secret:\).*/\1 <redacted>/'`.
- Treat the Security tab as one signal. "No real alerts" is not "no leak".
