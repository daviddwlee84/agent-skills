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
│   ├── bootstrap-project.sh                  # install pre-commit + gitleaks + redactor
│   └── scan-staged.sh                        # gitleaks wrapper with agent-friendly exit codes
├── references/
│   ├── transcript-session-discovery.md       # SpecStory / Claude session layouts
│   ├── pre-commit-redaction-stack.md         # layered defense design
│   └── remediation.md                        # rotate-first leak runbook
└── assets/
    ├── artifact-dirs.txt                     # configurable list of agent artifact dirs
    ├── pre-commit-config.yaml.template
    ├── gitleaks.toml.template
    └── redact_secrets.py                     # bundled copy; chezmoi is upstream
```

## Integration with chezmoi

The skill sits on top of the user's existing chezmoi infrastructure
(if present):

- `~/.config/git/hooks/pre-commit` (global `core.hooksPath`) runs the
  repo-level `.pre-commit-config.yaml` this skill installs.
- `~/.local/share/chezmoi/scripts/redact_secrets.py` is the upstream
  source of truth for the bundled redactor; `bootstrap-project.sh
  --from-chezmoi` symlinks rather than copies so fixes propagate.
- `~/.local/share/chezmoi/.gitleaks.toml` shares rule IDs with the
  skill's `gitleaks.toml.template` so `.gitleaksignore` / allowlist
  tweaks stay portable across repos.

For repos without chezmoi, `bootstrap-project.sh` produces a
self-contained stack.

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
