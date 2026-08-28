# Adding catalog entries

How to add or update entries in the [Catalog](../catalog/index.md) —
new external skills, new MCP servers, new domain hubs, or status
changes on existing entries.

This workflow couples the catalog to `vendor.yaml` and `TODO.md` (the
existing sources of truth) without duplicating them. Catalog pages are
the *vendoring decision log*; the actual vendoring happens via existing
scripts.

## When to write a catalog entry

| You discovered… | Where it goes | Status to start with |
|---|---|---|
| An external skill you might want to vendor | [`skill-collections.md`](../catalog/skill-collections.md) + relevant [domain hub](../catalog/domains/index.md) | `wishlist` |
| An interesting skill you explicitly do not want in routine discovery | [`curiosities.md`](../catalog/curiosities.md) | `skipped` with the docs-only reason |
| An MCP server you want to remember | New file under [`catalog/mcp/`](../catalog/mcp/index.md) + relevant domain hub | `wishlist` |
| A whole new professional domain | New file under [`catalog/domains/`](../catalog/domains/index.md) (copy `_template.md`) | (hub itself, not entry) |
| A skill you looked at and rejected | Add to `skill-collections.md` with reason | `skipped` |
| A skill you looked at but didn't decide on | Add to `skill-collections.md` with 1-line note | `evaluated` |

## Status enum

--8<-- "_snippets/external-install.md"

## Status change recipes

### `wishlist` → `deferred`

The entry has crossed into "we should evaluate this" territory.

```bash
./scripts/add-todo.sh --priority P? --effort <S|M|L> \
  --title "<skill-name> skill" \
  --description "Evaluate <upstream URL> for <use case>. See catalog/<page>.md."
```

Then edit the catalog entry: change `status: wishlist` → `status: deferred`,
link to the new TODO line.

### `deferred` → `vendored`

The entry has been evaluated and we want to vendor it.

```bash
# Vendor the skill (writes to vendor.yaml + downloads files)
./scripts/add-vendor.sh <owner>/<repo>/<path-to-skill>

# Or with a series subdir
./scripts/add-vendor.sh --series <series-name> <owner>/<repo>/<path-to-skill>

# If the entry had a TODO P? line, promote it
./scripts/promote-todo.sh --title "<substring>" \
  --summary "Vendored from <upstream URL>"
```

Then edit the catalog entry: change `status: deferred` → `status: vendored`,
update the link to point at `skills/vendor/<name>/` (or
`skills/vendor/<series>/<name>/`).

### `wishlist` / `evaluated` → `skipped`

You read the upstream and decided not to vendor.

Just edit the catalog entry: change status → `skipped`, add the reason
inline (one sentence). Examples:

- "Skipped — duplicates `<other-skill>` from `<more-authoritative-source>`."
- "Skipped — Slack-specific; not portable."
- "Skipped — narrower than `<existing-local-skill>` and overlaps it."

## Adding a new MCP entry

1. Create `docs/catalog/mcp/<slug>.md` with the YAML frontmatter
   schema documented in [`mcp/index.md`](../catalog/mcp/index.md#per-entry-conventions).
2. Fill the 6-section body (TL;DR / capabilities / install / when /
   related / sources).
3. Translate to `docs/catalog/mcp/<slug>.zh-TW.md`.
4. Add to the `mkdocs.yml` nav under `Catalog → MCP wiki`.
5. Add a row to the entries table in
   [`mcp/index.md`](../catalog/mcp/index.md).
6. Cross-link from any relevant domain hub's MCP section.

When the MCP wiki has 5+ entries, the index table will be regenerated
by a script (planned — see follow-up TODOs). Until then, edit the
table by hand.

## Adding a new domain hub

See the [How to add a new domain hub](../catalog/domains/index.md#how-to-add-a-new-domain-hub)
section in the Domains overview — the recipe lives next to the
template it references.

## Bilingual obligation

Every page in `docs/catalog/` (except the snippet and `_template.md`)
must have a `*.zh-TW.md` counterpart. The `mkdocs-i18n` plugin's
`fallback_to_default: true` means missing translations don't break the
build, but the project convention is that every published page has
both languages in the same PR.

## Validation

```bash
make docs-build       # strict mode catches missing snippets / broken links
make marketplace      # ensure no regression on vendor.yaml / marketplace.json
make kanban           # ensure TODO.md still parses
```

Open the served site (`make docs-serve`) and click through the new
entries' cross-links to verify they resolve.
