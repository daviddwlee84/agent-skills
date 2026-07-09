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
> # …or just one skill by name — list all names first with --list
> npx skills@latest add daviddwlee84/agent-skills/skills --list
> npx skills@latest add daviddwlee84/agent-skills/skills --skill clash-proxy-api
> ```
