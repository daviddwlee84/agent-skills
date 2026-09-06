# `sourcegraph-access-token` flags Git commit SHAs in agent transcripts

**Symptoms** (grep this section): `rule=sourcegraph-access-token` on a 40-hex
Git commit OID · hundreds of findings in `.specstory/history/*.md` · no `sgp_`
prefix in any reported line · a transcript about secret-scanner output cannot
pass its own pre-commit gate
**First seen**: 2026-09
**Affects**: gitleaks 8.30.1 default `sourcegraph-access-token` rule when an
agent artifact contains both its `sourcegraph` keyword and full Git OIDs
**Status**: fixed in `ahh-v2.0.1`; covered by
`TestSourcegraphCommitOidAllowlist`

## Symptom

Scanning a long SpecStory transcript reports many entries like:

```text
path=".specstory/history/<session>.md" line=<n> rule=sourcegraph-access-token
```

The reported source lines are ordinary `git log`, branch, or diagnostic output
containing full 40-hex commit OIDs. None contains a Sourcegraph `sgp_...` token.
A transcript that quotes the scanner's own findings can amplify the count on
each later run.

## Root cause

The upstream gitleaks rule accepts modern prefixed Sourcegraph tokens **and** a
legacy bare 40-hex alternative:

```regex
sgp_(...)|sgp_[a-fA-F0-9]{40}|[a-fA-F0-9]{40}
```

It also carries `sgp_` and `sourcegraph` keyword prefilters. Agent transcripts
routinely include the word `sourcegraph` while discussing scanner output, and
they routinely include full commit OIDs while capturing Git commands. Once both
appear in a scanned fragment, an indistinguishable bare-hex match is reported.

This is not safe to solve by allowlisting all 40-hex globally: outside archival
agent artifacts, a legacy bare-hex Sourcegraph token may be real.

## Workaround / fix

Use a targeted global allowlist that requires **all** of:

1. target rule is `sourcegraph-access-token`;
2. path is a configured agent-artifact root; and
3. finding `Secret` is exactly bare 40-hex.

```toml
[[allowlists]]
  targetRules = ["sourcegraph-access-token"]
  condition = "AND"
  paths = [<agent artifact roots>]
  regexes = ['''(?i)^[a-f0-9]{40}$''']
```

Do not set `regexTarget = "match"` here: the upstream rule's full `Match`
includes a trailing delimiter, while the default target is the extracted
`Secret`. A real `sgp_...` token does not match the bare-hex expression and
continues to fire inside artifact roots. The same bare 40-hex value outside
those roots also continues to fire.

## Prevention

Every scanner false-positive allowance needs a three-way regression test:

- the known false-positive shape is clean only in its intended path;
- the same shape still fires outside that scope; and
- a real credential shape for the targeted rule still fires inside the scope.

Run the test through `gitleaks git --staged`, matching production. `gitleaks
detect --no-git --source <file>` changes path resolution and can make a
path-scoped allowlist appear ineffective.

Also test the exact pinned binary. gitleaks v8.22.1 silently accepts but ignores
top-level `[[allowlists]]`; `targetRules` requires the newer schema used by the
v8.30.1 template pin. A config-parse smoke test alone cannot detect that skew --
it must assert both the allowed false positive and the still-blocked controls.
