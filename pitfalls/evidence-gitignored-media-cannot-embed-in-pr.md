# Screenshot from `.evidence/` renders as a broken image in a PR comment

## Symptom

An agent captures a demo screenshot with the `demo-evidence` skill, then
tries to show it in a pull-request comment by linking the file:

```markdown
![login demo](.evidence/claude-5f932f43/2026-…-login/login.png)
```

The image renders as a **broken-image icon** (or GitHub silently drops it).
The same is true for a raw URL to the file on the branch — GitHub returns
404, because the path was never pushed.

## Root cause

`demo-evidence` files bundles under `.evidence/`, which `new-bundle.sh`
adds to `.gitignore` **by design** (acceptance artifacts should never enter
git history). A gitignored file is:

- not committed, so there is no `raw.githubusercontent.com/<branch>/…` URL, and
- not part of the PR diff, so GitHub's Markdown image proxy (Camo) has
  nothing to fetch.

GitHub only inlines images from a public HTTPS URL or from a file the user
drag-drops into the comment box (which uploads to
`user-images.githubusercontent.com`). A local, gitignored path is neither.

## Workaround

The evidence bundle is meant to be reviewed **locally**, not embedded in a
PR. Pick one:

- **Local review (intended path):** point the reviewer at
  `<bundle>/MANIFEST.md`; they open it on a checkout of the branch.
- **Manual embed:** drag-drop the PNG into the PR comment box so GitHub
  uploads it to its own CDN, then paste the generated URL.
- **Out-of-band:** upload the media to any public HTTPS host (gist raw URL
  for images, a CDN/release asset for video) and reference that URL.

## Prevention / invariant

**Gitignored evidence has no public URL — never link a `.evidence/` path in a
PR/issue and expect it to render.** Automated PR posting that embeds media
must first publish the file to a durable URL, and must run a secret scan
first (screenshots/logs can leak). That capability is deliberately deferred:
see the `TODO P?` item *"demo-evidence: PR posting for evidence bundles"*.
For v1, treat `.evidence/` as a local-only acceptance surface.
