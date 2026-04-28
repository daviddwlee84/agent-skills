# How `npx skills` reads catalog metadata

This page captures the verified mechanism behind the grouped install UI
of `npx skills@latest add ...`. Everything below was confirmed by reading
the actual source of the npm package (`vercel-labs/skills`,
[`src/plugin-manifest.ts`](https://github.com/vercel-labs/skills/blob/main/src/plugin-manifest.ts)
and [`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts))
and the official [Claude Code plugin-marketplaces docs](https://code.claude.com/docs/en/plugin-marketplaces).

## TL;DR for this repo

- The grouped picker UI you see when running
  `npx skills@latest add daviddwlee84/agent-skills/skills` is driven by
  `skills/.claude-plugin/marketplace.json` — **inside** the `skills/`
  directory, not at the repo root.
- Every group header is `kebabToTitle(plugins[].name)`. Skills not listed
  under any plugin fall through to the **Other** group.
- Edit the manifest by hand; run `make marketplace` (= `bash
  scripts/validate-marketplace.sh`) to catch broken paths, duplicates, or
  on-disk skills that would silently fall under "Other".
- We do **not** ship `.claude-plugin/plugin.json` — that's only for
  single-plugin repos.

## How the CLI resolves the manifest path

The user's argument to `npx skills add` is parsed into `repo` + optional
`subpath`. For this repo:

```
npx skills@latest add daviddwlee84/agent-skills/skills
                       └────────── repo ──────────┘ └sub┘
```

Inside the CLI ([`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts)):

```ts
const searchPath = subpath ? join(basePath, subpath) : basePath;
// ...
const pluginGroupings = await getPluginGroupings(searchPath);
```

So when the install command **includes** a subpath, the CLI reads the
catalog from `<repo>/<subpath>/.claude-plugin/marketplace.json`.

| Invocation | Where the CLI looks for the manifest |
|---|---|
| `npx skills add anthropics/skills` | `<repo>/.claude-plugin/marketplace.json` |
| `npx skills add daviddwlee84/agent-skills/skills` | `<repo>/skills/.claude-plugin/marketplace.json` |
| `npx skills add foo/bar/some/dir` | `<repo>/some/dir/.claude-plugin/marketplace.json` |

This repo uses the second form because the `skills/local/` and
`skills/vendor/` trees live under `skills/`, not at the repo root.

!!! warning "Common pitfall"
    Putting `.claude-plugin/marketplace.json` at the repo root and then
    invoking the CLI with a subpath silently disables grouping — the
    file at the root is never read, and every skill ends up in **Other**.
    Match the manifest's location to the install command's subpath.

## Manifest shape

Reference: official [marketplace manifest schema](https://code.claude.com/docs/en/plugin-marketplaces).

```json
{
  "name": "<unique-marketplace-id>",
  "owner": { "name": "...", "email": "..." },
  "metadata": {
    "description": "...",
    "version": "1.0.0",
    "pluginRoot": "./"
  },
  "plugins": [
    {
      "name": "<group-name-kebab-case>",
      "description": "Short description of the plugin / category",
      "category": "<for Claude Code /plugin UI>",
      "tags": ["...", "..."],
      "source": "./",
      "strict": false,
      "skills": [
        "./relative/path/to/skill-dir",
        "./another/skill-dir"
      ]
    }
  ]
}
```

What the `npx skills` picker actually consumes:

| Field | Used by `npx skills`? | Used by Claude Code `/plugin` UI? |
|---|---|---|
| `metadata.pluginRoot` | yes (resolves `source`) | yes |
| `plugins[].name` | **yes — drives the group header label** | yes |
| `plugins[].source` | yes (must be a string starting with `./`; object/remote sources are skipped) | yes |
| `plugins[].skills[]` | yes (must start with `./`) | yes |
| `plugins[].description` / `category` / `tags` / `version` / `strict` | **no — pass through** | yes |

So `category` and `tags` are essentially free metadata for now: they cost
nothing to include in the manifest, and any future native consumer
(Claude Code's `/plugin` browser, downstream catalog tooling) can use
them without us migrating the file.

## Group header rendering — `kebabToTitle`

The picker turns each plugin `name` into a header label by splitting on
hyphens and titlecasing each token. So:

| `plugins[].name` | UI header |
|---|---|
| `document-skills` | Document Skills |
| `claude-api` | Claude Api |
| `ml-workflow` | Ml Workflow |
| `fullstack-nextjs` | Fullstack Nextjs |
| `notebooks` | Notebooks |

Pick names that titlecase legibly. `claude-api` → "Claude Api" is the
official upstream choice and ships in the user-facing UI of
`anthropics/skills`, so awkward casing is a known quirk; do not work
around it with weird name fields.

## "Other" — the auto-fallback group

Any SKILL.md the CLI discovers under the search root that is **not**
listed in any `plugins[].skills[]` entry shows up under the **Other**
group header. This is how `anthropics/skills`'s `template-skill` ends up
under "Other" — it's not listed in their manifest's `plugins[]`.

Use this to your advantage: a skill that doesn't fit any category yet
can simply be omitted from `marketplace.json` and it will still install,
just under "Other". Our `make marketplace` validator emits a warning (not
an error) for unlisted on-disk skills so they're easy to notice.

## Path resolution rules (gotchas)

- `source: "./..."` and `skills[]: "./..."` are **relative to the
  marketplace root** (the directory containing `.claude-plugin/`), not
  relative to the JSON file itself or the `.claude-plugin/` dir.
- The CLI rejects any path that does not start with `./` — `../` and
  absolute paths are not allowed (path-traversal protection in
  [`isContainedIn`](https://github.com/vercel-labs/skills/blob/main/src/plugin-manifest.ts)).
- `metadata.pluginRoot` (optional) is prepended to every plugin's
  `source`. We don't use it; we set `source: "./"` per plugin so each
  plugin path resolves directly under the manifest root (`skills/`).

## Reserved marketplace `name`s

These cannot be used as the `name` field, per official docs:

- `claude-code-marketplace`, `claude-code-plugins`,
  `claude-plugins-official`
- `anthropic-marketplace`, `anthropic-plugins`
- `agent-skills`
- `knowledge-work-plugins`, `life-sciences`
- Any name that impersonates an official marketplace
  (e.g. `official-claude-plugins`, `anthropic-tools-v2`)

This repo's manifest uses **`daviddwlee84-skills`** — the GitHub repo
folder is still allowed to be `agent-skills`; only the `name` field
inside the manifest is restricted. The validator script enforces this.

## Versioning

- If `metadata.version` is **omitted** and the marketplace is hosted in
  git, every commit is treated as a new version — users always see
  whatever's on `main`. This matches `anthropics/skills`.
- If `metadata.version` is **set**, users only see updates when the
  number changes (semver-style).

We currently set `metadata.version: "1.0.0"` as a baseline. To switch to
"every commit is latest" semantics, drop the field.

## `marketplace.json` vs `plugin.json`

| File | Purpose | When to use |
|---|---|---|
| `.claude-plugin/marketplace.json` | Catalog of multiple plugins / categories | Multi-category collections (this repo, `anthropics/skills`) |
| `.claude-plugin/plugin.json` | Manifest for a **single** plugin | Single-plugin repos (one bundle of skills, no grouping) |

The two files are not redundant. `anthropics/skills` ships only
`marketplace.json`; we do the same. A repo can technically ship both,
but for a multi-category catalog like this one, `plugin.json` is
unnecessary.

## Cross-agent portability

`npx skills` is a one-way installer: it reads the manifest, then copies
SKILL.md files into each target agent's native skills directory
(supported targets enumerated in
[`src/types.ts`](https://github.com/vercel-labs/skills/blob/main/src/types.ts)).
Other agents (OpenCode, Codex, Cursor, Aider, …) do **not** read
`.claude-plugin/marketplace.json` natively — they have their own
conventions (`.opencode/`, `AGENTS.md`, `.cursor/rules/`, etc.).

So the trade-off is:

- One `marketplace.json` is enough for cross-agent **install** via
  `npx skills add`.
- Native discovery in non-Claude agents requires whatever that agent
  expects, separate from this manifest.

If we ever need a second native catalog format, the cleanest
intermediate is to start treating `marketplace.json` as a *generated*
artifact from a canonical YAML and add a generator script. We have not
done that yet — single-consumer hand-edit is fine.

## Working with the manifest in this repo

```bash
# Validate the manifest (parses, name not reserved, all paths exist,
# no duplicates, on-disk skills covered).
make marketplace

# Or run the script directly with verbose output.
bash scripts/validate-marketplace.sh
```

After adding a new local or vendored skill:

1. Place the SKILL.md as usual under `skills/local/<name>/` or
   `skills/vendor/<name>/`.
2. Open `skills/.claude-plugin/marketplace.json` and add the new path
   (relative to `skills/`) to the appropriate plugin's `skills[]` array,
   **or** intentionally leave it out so it falls under "Other".
3. Run `make marketplace`. It will warn for unlisted skills and error
   for broken paths.

## Source references

- `npx skills` package source:
  [vercel-labs/skills](https://github.com/vercel-labs/skills) on GitHub,
  npm package
  [`skills`](https://www.npmjs.com/package/skills).
- Manifest read logic:
  [`src/plugin-manifest.ts`](https://github.com/vercel-labs/skills/blob/main/src/plugin-manifest.ts).
- Subpath + searchPath logic:
  [`src/skills.ts`](https://github.com/vercel-labs/skills/blob/main/src/skills.ts).
- Picker UI grouping:
  [`src/add.ts`](https://github.com/vercel-labs/skills/blob/main/src/add.ts)
  (search for `groupMultiselect` and `kebabToTitle`).
- Official Claude Code docs:
  [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces),
  [plugins-reference](https://code.claude.com/docs/en/plugins-reference).
- Reference manifest in this repo:
  [`skills/.claude-plugin/marketplace.json`](../../skills/.claude-plugin/marketplace.json).
