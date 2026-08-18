# agent-history-hygiene

Keep coding-agent chat transcripts and plan files committed alongside
the feature diff they produced, without leaking `.env` contents or API
keys into git history.

| Surface | Question it answers |
|---|---|
| `find-session.sh` | "Which transcript / plan file is *my* current session?" |
| `stage-agent-artifacts.sh` | "Which agent files belong in the next commit?" |
| `bootstrap-project.sh` | "How do I get pre-commit + gitleaks + redactor into a new repo?" |
| `scan-staged.sh` | "Is there a leaked secret in what I'm about to commit?" |
| `probe-specstory-redaction.py` | "What does SpecStory already redact, so we don't redo it?" |
| `references/remediation.md` | "I already pushed a secret — now what?" |

The skill exists to stop three common failure modes:

1. Agents silently **dropping** `.specstory/history/*.md` and
   `.claude/plans/*.md` from commits because they look like generated
   artifacts.
2. Accidental `.env` echoes inside chat transcripts that then get
   committed and pushed.
3. Reflexive `git push --force` after a leak — which doesn't actually
   revoke the credential and often destroys teammate work.

## When the skill triggers

- "Commit my chat" / "save the specstory session" / "stage the plan
  file" / "把 plan 跟 specstory 一起 commit 進去".
- Untracked `.specstory/history/*.md` or `.claude/plans/*.md` during a
  `git status`.
- "Scrub this transcript" / "redact my key" / "gitleaks flagged my
  chat history".
- "Set up pre-commit for this repo" / "bootstrap secret scanning".
- "I pushed a `.env`" / "a secret went to main" — the skill steers to
  the rotate-first runbook instead of a history rewrite.

## Structure

```
skills/local/agent-history-hygiene/
├── SKILL.md                                  # ~260 lines
├── scripts/
│   ├── find-session.sh                       # locate current SpecStory + Claude session
│   ├── stage-agent-artifacts.sh              # git-add the right artifacts
│   ├── bootstrap-project.sh                  # install pre-commit + gitleaks, wire the redactor
│   ├── probe-specstory-redaction.py          # measure SpecStory's own redaction coverage
│   └── scan-staged.sh                        # gitleaks wrapper with agent-friendly exit codes
├── references/
│   ├── transcript-session-discovery.md       # SpecStory / Claude session layouts
│   ├── pre-commit-redaction-stack.md         # layered defense design
│   ├── specstory-native-redaction.md         # what upstream redacts, measured
│   └── remediation.md                        # rotate-first leak runbook
└── assets/
    ├── artifact-dirs.txt                     # configurable list of agent artifact dirs
    ├── pre-commit-config.yaml.template
    ├── gitleaks.toml.template
    └── redact_secrets.py                     # run in place from the installed skill
```

## Integration with chezmoi

The skill sits on top of the user's existing chezmoi infrastructure
(if present):

- `~/.config/git/hooks/pre-commit` (global `core.hooksPath`) runs the
  repo-level `.pre-commit-config.yaml` this skill installs.
- `~/.local/share/chezmoi/scripts/redact_secrets.py` was the original
  upstream. `assets/redact_secrets.py` is now the source of truth and reaches
  consuming repos as a **pinned pre-commit hook** published from this repo's
  root `.pre-commit-hooks.yaml` — no vendored copy to drift.
  `bootstrap-project.sh --from-chezmoi` still symlinks the chezmoi
  `.pre-commit-config.yaml` / `.gitleaks.toml` for repos that prefer it.
- `~/.local/share/chezmoi/.gitleaks.toml` shares rule IDs with the
  skill's `gitleaks.toml.template` so `.gitleaksignore` / allowlist
  tweaks stay portable across repos.

For repos without chezmoi, `bootstrap-project.sh` produces a
self-contained stack. The redactor is **not** copied into the repo: the
generated `.pre-commit-config.yaml` references the hook by tag, so
`pre-commit autoupdate` ships fixes everywhere and the script path never
depends on where `npx skills` happened to install the skill.

```yaml
- repo: https://github.com/daviddwlee84/agent-skills
  rev: ahh-v1.1.0
  hooks:
    - id: redact-agent-secrets
```

`bootstrap-project.sh --migrate` converts a repo off the old vendored
`scripts/redact_secrets.py` layout.

## Default workflow: commit feature + chat together

```bash
# 1. Make sure the agent knows which session is "ours".
bash skills/local/agent-history-hygiene/scripts/find-session.sh

# 2. Stage code, then auto-add agent artifacts.
git add path/to/feature.ts
bash skills/local/agent-history-hygiene/scripts/stage-agent-artifacts.sh

# 3. Belt-and-suspenders secret scan.
bash skills/local/agent-history-hygiene/scripts/scan-staged.sh

# 4. Commit. Pre-commit re-runs redact + gitleaks as a catch-all.
git commit -m "feat: ..."
```

## SpecStory native redaction (v2.4.0+)

SpecStory ships its own secret redaction now, so this skill is no longer the
first line of defense for `.specstory/history/`.

| Ref | What |
|---|---|
| [PR #235](https://github.com/specstoryai/getspecstory/pull/235) | `feat(redaction): automatically redact secrets from saved markdown history` — community PR by [@warnes](https://github.com/warnes), merged 2026-07-20 |
| [PR #253](https://github.com/specstoryai/getspecstory/pull/253) | A `gofmt` CI-fix fork of #235; closed in favor of #235 |
| **v2.4.0** (2026-07-20) | Shipped **on by default**, via the [Betterleaks](https://github.com/betterleaks/betterleaks) ruleset, covering local markdown **and** cloud sync |
| [#274](https://github.com/specstoryai/getspecstory/issues/274) (open) | Adjacent leak vector — `specstory watch` exposes the cloud auth token in its process command line |

The merged code is not the PR's: the maintainer swapped its 11 inline regexes
for Betterleaks, and the PR's `extra_patterns` (custom regexes) did not survive
that rewrite. `[redaction] enabled` in `.specstory/cli/config.toml` — or
`--no-redact-secrets` — is the only knob.

### Measured coverage

`scripts/probe-specstory-redaction.py` synthesizes a Claude Code session,
renders it twice through `specstory sync --print` (with and without
`--no-redact-secrets`), and diffs per secret class. Against specstory 2.9.0,
over 54 class/context pairs:

| Caught by | Pairs | Examples |
|---|---:|---|
| SpecStory | 36 | Anthropic, OpenAI, GitHub PAT/OAuth/Actions, GitLab, Google, Groq, Slack, Stripe, Supabase, Linear, PEM blocks, `.env` dumps |
| **Ours only** | 15 | Cursor, Tailscale, Discord/Zapier/Make webhooks — plus HuggingFace, Notion, WakaTime, OpenAI project keys **in prose** |
| Nobody | 3 | `AKIA…` access key IDs; Telegram bot tokens in prose |

The structural finding: Betterleaks catches several classes only in
`KEY=value` form, via an entropy-based `generic-api-key` rule. The same token
in a sentence — which is how a tool transcript actually prints one — sails
through. Our prefix-anchored rules don't care about surrounding syntax.

### How the two layers stay out of each other's way

Both write the same sentinel, `[REDACTED:<rule-id>]` (SpecStory's binary
carries the format string `[REDACTED:%s]`), and `.gitleaks.toml` allowlists
that shape. A transcript SpecStory already cleaned passes through the hook
untouched — no "files were modified by this hook", no re-`git add`, no second
commit.

The redactor writes `[REDACTED:<rule-id>]` instead of `sk-abc...xyz`
truncations, and PEM blocks become `[REDACTED:private-key]` — the exact label
SpecStory uses. The truncated form still appears in the console report, where a
fingerprint helps identify which credential to rotate. `--legacy` writes the
pre-2.4.0 placeholders instead; it changes only the bytes written, never what
is detected.

(The related rule that a bare `PRIVATE KEY` *mention* is not key material —
`detect-private-key` greps for `BEGIN … PRIVATE KEY` headers — is enforced
separately by the redactor's header-scoped matching.)

## Post-leak discipline

`scan-staged.sh` exit codes branch on leak state (0 clean, 10 redacted,
20 leaks, 30 no gitleaks). When a leak slips through:

1. **Rotate at the provider.** The only act that revokes the
   credential. Links in `references/remediation.md` §1.
2. **Assess blast radius.** Local/unpushed? Feature branch? Main?
3. **Scrub only if cheap.** Amend or `reset --soft` on unpushed commits;
   `git filter-repo` + force-with-lease on feature branches; **never**
   rewrite `main`.

The runbook explicitly forbids `git push --force` against shared
branches — see `references/remediation.md` §5.

## Gotchas

- SpecStory ≥ 2.4.0 already redacts on write — don't let the hook redo it.
  See [SpecStory native redaction](#specstory-native-redaction-v240) above.
- A bare "PRIVATE KEY" mention is not a leak; `detect-private-key` matches
  `BEGIN … PRIVATE KEY` only. Redacting prose churned transcripts for nothing.
- Claude Code `plansDirectory` project-level is sometimes ignored
  ([issue #19537](https://github.com/anthropics/claude-code/issues/19537));
  set at the user level (`~/.claude/settings.json`) as the default.
- `gitleaks protect` is deprecated since v8.19.0 — use `gitleaks git
  --staged`. The skill uses the modern syntax everywhere.
- `pre-commit install` is per-clone — each teammate (and CI) must run
  it for hooks to fire.
- Global `core.hooksPath` runs the repo's `.pre-commit-config.yaml`
  only if it exists; a bare repo is unprotected until bootstrap.

## See also

- [Source](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/agent-history-hygiene)
- [`project-knowledge-harness`](project-knowledge-harness.md) —
  complementary memory harness that references `.claude/plans/` as
  ephemeral scratchpads. This skill closes the loop by making sure
  those scratchpads actually land in git.
