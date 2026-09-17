# PRO sources and synchronization

Read this for `vectorbtpro` development or private documentation synchronization.

- AI integration: https://members.vectorbt.pro/using-ai/
- Downloads: https://members.vectorbt.pro/downloads/
- Knowledge assets: https://members.vectorbt.pro/cookbook/knowledge/
- Releases and source: https://github.com/polakowo/vectorbt.pro/releases

The helper uses `gh api` and `gh release download`, including gh's existing
keyring/environment credentials. It never extracts a token. If access fails,
check `gh auth status` and the account's accepted repository invitation.
Website sign-in alone does not grant GitHub access; a 404 may be an access error.
An offline probe reports unknown access, not denial.

## Sync contract

`sync-pro --python /project/.venv/bin/python` imports PRO in that interpreter to
select its release. `--release` selects a concrete snapshot without requiring a
VBT installation. When both are passed, the explicit release wins: label any
difference from the runtime and don't use it as proof of installed API behavior.
The helper never installs or upgrades the library.

Defaults are `--assets pages,examples`; `--messages` adds Discord history. For
older releases that have no examples export, use `--assets pages`. Do not fill
missing assets from another release. An already cached optional asset continues
to be checked on refresh so MCP and normal development do not drift apart.

Use the JSON-returned paths, not an assumed generation path. Cache layout:

```text
<XDG_CACHE_HOME or ~/.cache>/vectorbt-agent/pro/<release>/
  manifest.json
  .lock
  generations/<generation>/
    raw/{pages,examples,messages}.json.gz
    markdown/pages/*.md
    markdown/examples/*.md
    markdown/messages.jsonl        # only with messages
    index.jsonl
```

The manifest selects a complete generation atomically. Previous generations
remain available for active readers/MCP processes. They are disposable caches;
remove obsolete release caches only when no process uses them. A document sync
does not put private exports in the skills repository or project Git history.

- `cached`: validated local files, last metadata check within 24 hours.
- `unchanged`: GitHub metadata checked now; existing generation remains valid.
- `updated`: changed assets downloaded, checked and rendered into a new generation.
- `offline`: explicitly requested valid local cache, no remote freshness claim.
- `stale`: remote metadata failed; existing valid cache remains usable. Report it.
- Invalid checksums/JSON fail with exit 4 and leave the previous manifest intact.

`--refresh` bypasses the 24-hour check interval but doesn't redownload unchanged
assets. `--dry-run` reads metadata and reports planned locations without writing.
The helper compares asset IDs, timestamps, size and digest. Missing remote
digest is recorded as `remote_checksum_verified: false`; local SHA-256 still
detects subsequent corruption. Unsupported/broken JSON is not silently activated.

## Reading the exported context

Search `index.jsonl` for exact API names or URL fragments, then use its relative
path and line to read the content under the generation directory. Search page
Markdown for unknown names. Pages preserve parent/child heading order and source
URLs; examples retain their descriptions and upstream verification metadata.

Discord messages are JSONL to avoid creating thousands of tiny files. Parse
matching rows with Python to read unescaped content and follow their reply /
thread metadata; a single support message is not an API contract. Normal coding
should begin with API pages, cookbook sections and local source.

The same assets can be used with native `PagesAsset.from_json_file()` and related
classes when the target VBT version supports them. Simply placing files in an
arbitrary folder does not reconfigure native `pull()`; the MCP launcher explicitly
sets each asset's directory. Native CLI calls outside that launcher use their
own VBT settings/cache unless explicitly configured.

Once VBT is installed, `python -m vectorbtpro mcp --help` discovers native tools
on versions that ship the CLI. Use object/page lookup for known targets and
`search_method="bm25"` for literal API queries. Embeddings are optional and must
use compatible model/dimensions/snapshots if requested later.
