# Global `pre-commit` hook silently skips repos that have no `.pre-commit-config.yaml` or `.gitleaks.toml`

**Symptoms** (grep this section): `git commit` of a transcript or plan succeeds
with **zero** scanner output · `git config --get core.hooksPath` is a global
directory · `ls .pre-commit-config.yaml .gitleaks.toml` → `No such file or
directory` · secrets are found only later, by an audit or a GitHub alert · the
repo that *ships* a secret-scanning skill has no scanner config of its own
**First seen**: 2026-10
**Affects**: a machine with one global `core.hooksPath` whose `pre-commit` hook
delegates to repo-local config (here a chezmoi-managed
`~/.config/git/hooks/pre-commit`)
**Status**: active

## Symptom

```console
$ git config --get core.hooksPath
~/.config/git/hooks
$ ls .pre-commit-config.yaml .gitleaks.toml
ls: .pre-commit-config.yaml: No such file or directory
ls: .gitleaks.toml: No such file or directory
$ git commit -m "docs: add session transcript"   # succeeds, prints nothing from any scanner
```

Silence looks exactly like "scanned and clean". In the audit behind this note,
running the skill's own gitleaks config over that repo's history reported 278
occurrences of 51 distinct values — including a real credential — and every one
had been committed through this silent path. The same config run at commit time
would have flagged the real one.

## Root cause

The global hook is opt-in by file presence. Paraphrased:

```sh
if [ -f .pre-commit-config.yaml ]; then
    command -v pre-commit && exec pre-commit run --config .pre-commit-config.yaml
fi
if [ -f .gitleaks.toml ] && command -v gitleaks; then
    gitleaks git --staged --verbose || exit 1
fi
exit 0
```

With neither file, both branches are skipped and the hook exits `0` without a
word. That is a deliberate design (do not force a scanner onto every repo), but
it makes "no scanner ran" indistinguishable from "scanner passed".

Two details that matter:

- `exec pre-commit run …` replaces the shell, so when a `.pre-commit-config.yaml`
  exists the `.gitleaks.toml` branch never runs — the pre-commit config must
  carry its own gitleaks hook.
- The repo that distributes `agent-history-hygiene` had never run its own
  `bootstrap-project.sh`, so it sat in the skipped state while committing
  transcripts all day.

## Workaround / fix

1. **Detect it.**

   ```bash
   [ -f .pre-commit-config.yaml ] || [ -f .gitleaks.toml ] \
     || echo "NO SECRET SCAN ON COMMIT"
   ```

2. **Bootstrap the repo, without `--install-hook`.**

   ```bash
   bash skills/local/agent-history-hygiene/scripts/bootstrap-project.sh
   pre-commit run --all-files
   ```

   `--install-hook` is refused when `core.hooksPath` is set (by design, see the
   skill's gotchas) and is unnecessary here: dropping the config files in is
   what makes the global hook start delegating.
3. **Decide a baseline for existing transcripts** before turning the gate on:
   redact, or allowlist reviewed fingerprints. Running `--all-files` on a repo
   with months of transcripts will, correctly, light up.
4. **Prove it fires** once, with a throwaway file carrying a canary assembled at
   runtime (never commit one), rather than assuming.

## Prevention

- Make the silent branch loud: have the global hook print one line to stderr
  when neither file exists. That change belongs in the managed dotfiles hook,
  not in this repo.
- Add a CI job running `gitleaks git` over all refs. A per-clone hook is never
  the last gate.
- Dogfood: a repo that ships a scanning skill should run it. See also
  [`github-secret-scanning-misses-generic-credentials-in-agent-transcripts`](github-secret-scanning-misses-generic-credentials-in-agent-transcripts.md).
