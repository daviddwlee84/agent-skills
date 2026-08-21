# Context

`lencx/skills` demonstrates two real platform adapters over one `skills/` tree: Claude Code uses `.claude-plugin/{marketplace,plugin}.json`, while current Codex uses `.codex-plugin/plugin.json`. Its `package-codex-plugin.sh`, however, only makes a custom ZIP that is neither a documented Codex install unit nor published by that repository.

This repository already has the portable distribution path it needs: `npx skills@latest add daviddwlee84/agent-skills/skills` installs individual skills for Claude Code, Codex, and other agents, and `skills/.claude-plugin/marketplace.json` is also a valid Claude Code `strict: false` multi-plugin marketplace. The gap is that only the `npx skills` use is documented and validated; native Claude installation has not been smoke-tested. Because the manifest lives under `skills/`, Claude's GitHub shorthand (`claude plugin marketplace add daviddwlee84/agent-skills`) cannot find it at the repository root.

**Decision:** keep `npx skills` as the primary cross-agent channel; support the existing manifest as an optional Claude Code native marketplace from a local checkout; do not add a duplicate root marketplace, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, or a ZIP packager. Codex already consumes the canonical `.agents/skills` installation, so a Codex-native bundle should only be reconsidered when marketplace discovery or another concrete native-only requirement exists.

## Implementation review update (2026-08-21)

Runtime review superseded two assumptions in the approved plan without changing its no-duplication goal:

- Claude Code 2.1.235 ignores top-level `metadata.version` for inline plugin identity; precedence is per-plugin `plugin.json`, `plugins[].version`, then git SHA. A fixed `"1.0.0"` did not block updates, so the implementation keeps the existing field and corrects the EN/zh-TW reference text instead of removing it.
- Codex 0.147.0 directly consumes this nested Claude-format marketplace from a local `skills/` path. On install it generates a cache-local `.codex-plugin/plugin.json` containing only the selected category's `skills[]`. The implementation therefore documents and smoke-tests both native CLIs while still adding no source `.codex-plugin` manifest or ZIP.
- `skills@1.5.23 --list` reconciled an existing agent-managed project despite its read-only-looking flag. Verification now runs from a disposable directory, and the symptom/workaround is recorded in `pitfalls/skills-list-reconciles-existing-project.md`.

The original implementation bullets below capture the approved starting point; this update records the verified deviations used by the final diff.

## Implementation

### 1. Make the existing Claude marketplace safe to publish natively

- In `skills/.claude-plugin/marketplace.json`, retain the current category entries, `source: "./"`, explicit skill paths, and `strict: false` shared-root design.
- Remove the permanently fixed `metadata.version: "1.0.0"` so a git-backed marketplace follows source revisions instead of appearing frozen unless someone manually bumps a second version.
- Do not add per-category `plugin.json` files: the inline `strict: false` entries already define these manifest-less skill bundles.

### 2. Add an isolated app-native smoke test

Create `scripts/smoke-claude-marketplace.sh` following the repository's strict-shell and temp-directory conventions. It will:

1. Require `claude` and `jq`, then run `claude plugin validate skills --strict`.
2. Set temporary `HOME` and `CLAUDE_CONFIG_DIR` values so marketplace registration and plugin installation cannot touch the user's real Claude configuration.
3. Register the local `skills/` directory as a marketplace.
4. Compare `claude plugin list --available --json` against plugin names derived from `skills/.claude-plugin/marketplace.json` rather than a hard-coded category count.
5. Install the small representative plugin `version-control@daviddwlee84-skills` and inspect it through Claude's plugin CLI, asserting that the expected `git-workflow` skill is exposed and unrelated category skills do not leak in.
6. Remove all temporary state on exit and emit actionable diagnostics on failure.

Add a `native-claude-smoke` target to `Makefile`, separate from `make validate` so local contributors without Claude Code can still run the portable publish gates. Update `.github/workflows/validate.yml` to install a pinned Claude Code CLI and run the smoke test; include the affected install/reference docs in its path filters so claims about this channel remain tested.

### 3. Document the channel boundary instead of duplicating catalogs

- `README.md` and `docs/_snippets/install.md`: keep the `/skills` `npx` command first; explain that it remains the recommended cross-agent/per-skill route and that Codex receives skills through `.agents/skills`. Add an optional Claude native workflow using a checkout plus `claude plugin marketplace add ./agent-skills/skills` and `claude plugin install <category>@daviddwlee84-skills`. Warn that native Claude installs a category plugin, not one arbitrary skill.
- `README.md`: replace the stale seven-group inventory with wording derived from or pointing at the manifest, avoiding another hard-coded count.
- `docs/reference/npx-skills-metadata.md`: distinguish the `npx skills` search root from Claude Code's marketplace root; explain why the nested manifest works from a local path but not the repository GitHub shorthand or a raw nested JSON URL with relative sources. Refine the `marketplace.json` versus `plugin.json` discussion to state that this repository omits per-plugin manifests because its entries are inline `strict: false` bundles.
- `CLAUDE.md` (and therefore symlinked `AGENTS.md`): correct the overview install command to include the required `/skills` suffix.

## Explicit non-goals

- No root `.claude-plugin/marketplace.json`: it would duplicate the category/skill inventory and require path rewriting; add one only if remote Claude shorthand becomes a real requirement, and then generate it from one canonical inventory.
- No `.codex-plugin/plugin.json` yet: it is an official Codex-specific adapter, but it provides no needed capability beyond this repository's current `npx` → `.agents/skills` path.
- No `package-codex-plugin.sh`, ZIP, or `.plugin` archive: Codex's public CLI installs through marketplaces and does not accept such an archive as a standard install unit.
- No blanket generation of `agents/openai.yaml`; that optional per-skill UI metadata is independent of catalog packaging.
- Existing adjacent issues (nested `upstream/SKILL.md` discovery and global Codex length-limit CI) stay outside this focused change.

## Verification

Run end to end:

```bash
make validate
make native-claude-smoke
npx skills@latest add daviddwlee84/agent-skills/skills --list
uv run mkdocs build
```

Acceptance checks:

- `claude plugin validate skills --strict` passes.
- The isolated smoke sees exactly the plugin names declared by the manifest and installs `version-control` without touching real `~/.claude` state.
- The installed plugin exposes `git-workflow` without cross-category skill leakage.
- `npx skills --list` still resolves the existing grouped collection from the `/skills` subpath.
- README and rendered docs present `npx skills` as primary, Claude local-native as optional, and Codex standalone consumption via `.agents/skills` without implying that a ZIP is standard.

Before any eventual commit, keep the automatically generated `.specstory` transcript/plan artifacts with the implementation diff and run the existing `agent-history-hygiene` staged-secret scan; they are review artifacts, not product scope.
