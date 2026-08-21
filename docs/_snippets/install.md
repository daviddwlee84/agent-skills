```bash
# Install all skills bundled in this repo into your project's
# .agents/skills/ directory.
npx skills@latest add daviddwlee84/agent-skills/skills
```

> **Note**
> The trailing `/skills` matters. Without it, `npx skills` will look in
> `.agents/skills/` of the upstream repo, which contains a different
> layout. The `skills/` suffix points the installer at the
> `skills/local/` and `skills/vendor/` trees.

This is the recommended cross-agent install path. Project installs place the
canonical skill content under `.agents/skills/`, which Codex reads directly;
Claude Code receives its corresponding `.claude/skills/` links.

> **Heads-up — upstream picker bug.**
> `npx skills`' interactive multiselect glitches once the skill list is long
> enough to scroll: options render duplicated and the selection state gets
> corrupted ([vercel-labs/skills#969](https://github.com/vercel-labs/skills/issues/969)).
> This repo ships enough skills to trigger it. Until it's fixed upstream, skip
> the picker:
>
> ```bash
> # Install everything, non-interactively (no picker)
> npx skills@latest add daviddwlee84/agent-skills/skills --yes
>
> # List names from a disposable directory. In an existing agent-managed
> # project, skills@1.5.23 may reconcile .agents/skills even with --list.
> scratch="$(mktemp -d)"
> (cd "$scratch" && npx skills@latest add daviddwlee84/agent-skills/skills --list)
> rm -rf "$scratch"
>
> # Install one skill by name.
> npx skills@latest add daviddwlee84/agent-skills/skills --skill clash-proxy-api
> ```

### Optional: native Claude Code and Codex marketplaces

A local checkout can expose the same category catalog through either native
plugin CLI:

```bash
git clone https://github.com/daviddwlee84/agent-skills.git

# Claude Code
claude plugin marketplace add ./agent-skills/skills
claude plugin install version-control@daviddwlee84-skills

# Codex (verified with 0.147.0)
codex plugin marketplace add ./agent-skills/skills
codex plugin add version-control@daviddwlee84-skills
```

Both native routes install a whole category plugin (`version-control` in this
example), not an arbitrary single skill. Codex reads the existing Claude-format
marketplace and generates its `.codex-plugin/plugin.json` adapter inside the
plugin cache; this repository does not need to maintain that second manifest.
Keep using `npx skills` when you want one skill or a cross-agent installation.

Pass the checkout's `skills/` directory, not the repository root: the catalog
intentionally lives under `skills/.claude-plugin/` for the `npx` subpath above,
and both native CLIs require a supported manifest at the marketplace source
root.
