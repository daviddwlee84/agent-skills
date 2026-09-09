# Adding owned skills

Use `owned` when a skill belongs with another project you maintain. The source
project evolves the instructions alongside its code; this collection supplies
discovery, grouped installation, documentation, and a reviewed distribution copy.

| Category | Canonical location | Editing rule |
|---|---|---|
| `local` | This repository | Edit `skills/local/<name>/` |
| `owned` | Another first-party repository | Edit there; sync into `skills/owned/<name>/` |
| `vendor` | A third-party repository | Follow upstream; sync into `skills/vendor/<name>/` |

Ownership is explicit through `collection: owned`, not inferred from a username.
`vendor.yaml` retains its historical filename and serves both upstream categories;
omitting `collection` preserves existing vendor behavior. `series`, `license_path`
and `frozen` work in either category.

## Start in the source project

For a skill useful while developing that project, put the canonical directory in
`.agents/skills/<name>/`, with an optional `.claude/skills/<name>` discovery link.
Use `skill-author` with explicit project scope:

```bash
bash skills/local/skill-author/scripts/new-skill.sh \
  --project --root /path/to/source-project userscript-development
```

Write and validate the skill in that project. Publish its canonical files before
enrolling an ordinary remote sync source. Then, from this collection:

```bash
./scripts/add-vendor.sh --owned \
  daviddwlee84/Tampermonkey-Scripts/.agents/skills/userscript-development
```

Add `./owned/userscript-development` to the appropriate marketplace plugin's
`skills[]`, add bilingual docs and navigation, and run `make validate` plus
`make docs-build`. A series uses `./owned/<series>/<name>`.

## Bootstrap before the first upstream publication

A skill being authored across two local repositories does not yet have a remote
commit containing its new files. Do not record an unrelated HEAD as `last_sync`.
For this initial state only:

1. Finish and validate the source project's canonical directory.
2. Copy its actual files into `skills/owned/<name>/` and verify byte equality.
3. Add the source entry with `collection: owned`, `pending_upstream: true`, and
   empty `last_sync.date` / `last_sync.commit`.
4. Keep developing in the source project; refresh the bootstrap copy when needed.

```yaml
skills:
  - name: userscript-development
    collection: owned
    pending_upstream: true
    upstream:
      owner: daviddwlee84
      repo: Tampermonkey-Scripts
      path: .agents/skills/userscript-development
      branch: main
    last_sync:
      date: ""
      commit: ""
```

Routine `make sync` / `make sync-check` explicitly report pending and preserve the
bootstrap files. After the source is published, activate the named entry:

```bash
./scripts/sync-vendor.sh --activate userscript-development
```

Activation performs a real remote sync and clears pending only after success.
An unpublished path or failed download leaves the existing copy intact. Review
the diff before publishing this collection. Pending is for an unpublished owned
source; `frozen` is for an upstream intentionally no longer being followed.

## Normal update loop

1. Update and validate the canonical skill with the source project's change.
2. Publish that source change through the project's normal workflow.
3. Run `./scripts/sync-vendor.sh --check userscript-development`, then
   `./scripts/sync-vendor.sh userscript-development` here.
4. Review the mirrored diff and recorded upstream SHA, run publish gates, and
   publish this collection through its normal workflow.

The existing weekly sync workflow also covers active owned entries and opens a
reviewable PR. Sync fetches the skill tree from the recorded commit and stages
downloads before replacing the last good copy.

The distribution copy contains real files. Cross-repository symlinks would refer
to paths absent from downstream installations. Do not add a second canonical
`skills/local/<name>` copy or load the skill into this collection's own discovery
directories unless maintaining this collection actually needs it.

After publication, users can install from this collection's grouped picker or
directly from the source project. The skill name stays `userscript-development`;
changing its upstream source can still require an explicit reinstall/lock review.

## Maintainer verification

`make test-source-sync` runs offline fixtures with a fake GitHub CLI and real
`yq`: default vendor routing, owned/series routing, check mode, pending activation,
failed-download preservation, frozen entries, destination validation, and
`add-vendor.sh --owned`. It requires Python 3 and mikefarah/yq.
