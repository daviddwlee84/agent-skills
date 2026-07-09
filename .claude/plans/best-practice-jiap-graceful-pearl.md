# Best practice: keep fake secret test-vectors out of scan scope by default

## Context

`skills/local/agent-history-hygiene/tests/fixtures/` ships **deliberately-fake,
realistic-shape** secrets (`real_anthropic.md`, `real_openai.md`,
`private_key.md`, `webhook_urls.md`). They exist so the skill's gitleaks rules +
redactor have a corpus to fire against — but a secret scan can't tell all-`a`
filler from a real leak, so every scan of this repo re-flags them. A recent
triage burned effort confirming 11 such hits were harmless.

Today the only thing holding the line is the repo-root **`.gitleaksignore`**, using
brittle `file:rule:line` fingerprints. It is fragile (one entry,
`real_openai.md:openai-project-key:9`, is **already stale** — the key is on
line 8), covers only one gitleaks scan-mode, is honored by neither GitHub-native
secret scanning nor Socket nor `/security-review`, and **never ships**, so a
downstream `npx skills add` install can trip a user's freshly-bootstrapped
gitleaks hook on the copied fixtures.

**Principle to implement:** fake test-vectors are out of scan scope *by default*,
and only "fire" when a test *specifically re-plants* them. The tests already do
the re-planting half (they copy fixture **content** into a throwaway repo at
unrelated paths, never scanning `tests/fixtures/` in place). This change adds the
missing half: an inline `gitleaks:allow` marker that **travels with each fixture**
(so the suppression reaches downstream installs too), which the tests **strip
before staging** so the rules still fire and every existing assertion still passes.

All mechanics below were empirically verified against gitleaks 8.30.0 (marker
suppresses; strip is byte-identical via sha match; `.py` comment leaves the
string value unchanged and `ast.parse`s; final marked tree scans COUNT 0).

## Approach (recommended)

Inline marker + strip-on-stage is the primary mechanism. `.gitleaksignore` is
deleted (superseded). A repo-root `.gitleaks.toml` is **assessed and declined**
(markers already make a default-rule root scan clean; adding one re-introduces
the blanket path-suppression we're replacing). `.github/secret_scanning.yml` is
**added defensively** — GitHub-native scanning is the one layer the marker can't
cover. Convention is codified so a future edit doesn't silently re-break it.

### 1. Mark the four firing fixtures
Append ` <!-- gitleaks:allow -->` (single leading space) after the secret on each
firing line. HTML-comment form renders invisibly in Markdown and reads as a
deliberate annotation; the leading space is the separator the strip regex reclaims.
- `tests/fixtures/real_anthropic.md` — line 6 (after the `sk-ant-…AA` key)
- `tests/fixtures/real_openai.md` — line 8 (after the 100-char `sk-proj-…` key)
- `tests/fixtures/private_key.md` — line 7 only (`-----BEGIN RSA PRIVATE KEY-----`);
  rule anchors on the BEGIN line, covers the whole block. Leave lines 8–10 alone.
- `tests/fixtures/webhook_urls.md` — each of lines 13,14,15,16,17.
- **Do NOT touch** `clean.md` / `example_shapes.md` (no marker → strip is a no-op →
  they keep their must-not-fire behavior).

### 2. Strip the marker in the Python corpus test
`tests/test_gitleaks_corpus.py` — add a module regex and rewrite `_stage_fixture_at`
(lines 27–32) to read → strip → write instead of `shutil.copy`:
```python
_GITLEAKS_MARKER_RE = re.compile(r"[ \t]*<!--[ ]?gitleaks:allow[ ]?-->")
# in _stage_fixture_at:
text = fixture_path.read_text(encoding="utf-8")
dest.write_text(_GITLEAKS_MARKER_RE.sub("", text), encoding="utf-8")
```

### 3. Strip the marker in the shell test
`tests/test_scan_staged.sh` — in `stage_fixture` (lines 50–55) replace `cp` with a
BSD/macOS-sed-safe strip (line-based, can't eat newlines):
```bash
sed 's/[[:space:]]*<!-- *gitleaks:allow *-->//g' "$FIXTURES/$fixture" > "$repo/$dest_rel"
```

### 4. Mark the two PEM headers in the redactor unit test
`tests/test_redact_secrets.py` — append `  # gitleaks:allow` to physical lines 70
and 142 (the `"-----BEGIN RSA PRIVATE KEY-----\n"` literals). This file never
stages into a throwaway repo (it writes its own strings to `tmp_path`) and never
ships downstream, so the comment is permanent — no strip needed, and it's a valid
Python comment that leaves the string value untouched. (The other inline `sk-…`
shapes are split concatenations like `"sk-proj-" + "A"*90`, so no contiguous key
exists in source — they don't fire and need no marker.)

### 5. Delete `.gitleaksignore`
Remove the repo-root file entirely — all 9 fingerprints are replaced by markers.
Trimming would leave a second, drift-prone source of truth.

### 6. `.gitleaks.toml` — assessed, do NOT add
With steps 1–4 a default-rule root scan is already clean (verified COUNT 0). A
root config would duplicate the skill's `assets/gitleaks.toml.template` and, if it
carried a `tests/fixtures/` path-allowlist, re-introduce blanket path-suppression.
Confirmed it also can't interfere with the tests (both pass an explicit `--config`
pointing at their throwaway repo's own copy). If root CI/pre-commit scanning is
ever added later, use `[extend] useDefault=true` with **no** fixtures allowlist.

### 7. Add `.github/secret_scanning.yml` (defensive)
GitHub-native scanning honors neither the marker nor `.gitleaksignore`. New file:
```yaml
paths-ignore:
  - "skills/local/agent-history-hygiene/tests/fixtures/**"
  - "skills/local/agent-history-hygiene/tests/test_redact_secrets.py"
```
Harmless if secret scanning isn't enabled on the remote; free for public repos.

### 8–10. Codify the convention (per Q2 = "codify")
- **`tests/README.md`** — add a "Test-vector hygiene" section after "## Layout":
  explain the marker, that the tests strip it before staging, and the hard
  invariant: **the strip must be byte-identical — never change a secret's length**
  or the length-sensitive rules (`sk-proj-…{80,}`, `sk-ant-…{93}AA`, webhooks) stop
  matching. Note GitHub scanning is excluded separately.
- **`docs/reference/skills-risk-evaluations.md` + `.zh-TW.md`** — extend the existing
  page (it already narrates why these fake secrets are checked in and names the
  fixtures) with a short "keeping fixtures out of scan scope" subsection. Bilingual
  pair is required for published `docs/`. No new page, no `mkdocs.yml` nav change.
- **`pitfalls/gitleaks-fires-on-checked-in-test-fixtures.md`** (new, symptom-first
  slug) — four-section format (verbatim symptom incl. Socket/downstream-hook
  variants → root cause incl. the stale-fingerprint drift → workaround = markers +
  strip + `secret_scanning.yml` → prevention = the byte-identical invariant). Add its
  row to `pitfalls/README.md`'s index table with grep keywords.

## Files
- Edit: `skills/local/agent-history-hygiene/tests/fixtures/{real_anthropic,real_openai,private_key,webhook_urls}.md`
- Edit: `skills/local/agent-history-hygiene/tests/test_gitleaks_corpus.py` (`_stage_fixture_at` + regex)
- Edit: `skills/local/agent-history-hygiene/tests/test_scan_staged.sh` (`stage_fixture`)
- Edit: `skills/local/agent-history-hygiene/tests/test_redact_secrets.py` (lines 70, 142)
- Edit: `skills/local/agent-history-hygiene/tests/README.md`
- Edit: `docs/reference/skills-risk-evaluations.md` + `docs/reference/skills-risk-evaluations.zh-TW.md`
- Delete: `.gitleaksignore`
- New: `.github/secret_scanning.yml`
- New: `pitfalls/gitleaks-fires-on-checked-in-test-fixtures.md` + row in `pitfalls/README.md`

## Verification
1. `make test-skill` — corpus pytest (`openai-project-key` / `anthropic(-strict)` /
   4 webhook rules fire; `clean` + `example_shapes` empty) and shell test
   `pass: 5 / fail: 0`. This is the primary proof the strip preserves firing.
2. Root scan clean on the marked tree: `git add -A && gitleaks git . --staged
   --no-banner --exit-code 1` → exit 0 / "no leaks found".
3. Byte-identity guard (optional): diff a stripped staged fixture against a
   marker-free reference — must be empty.
4. If gitleaks isn't installed: the corpus test `skipif`s and the shell test runs
   only its exit-30 case (by design). Fall back to the byte-identity check
   (`git`/`sed`/`python3` only) and note the deferral in the PR.

## Risks (and how the plan avoids them)
- **Strip not byte-identical** → rules stop matching. Regex reclaims the leading
  separator; sha-identical on all six fixtures; `sed` is line-based (verified).
- **Marker on wrong PEM line** → not suppressed. `private-key` anchors StartLine=7;
  marker on the BEGIN line covers the span (verified).
- **`.py` marker changes the written string** → redactor assertions fail. It's a
  comment after a string literal; value unchanged, `ast.parse` OK (verified).
- **Future edit adds a firing line without a marker** → scan re-breaks. Mitigated by
  the `tests/README.md` invariant + pitfalls entry.
