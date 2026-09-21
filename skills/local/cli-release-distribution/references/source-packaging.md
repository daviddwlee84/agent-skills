# Source packages and Go module downloads

Use when a distribution contains large development records or when adding a
checksummed source asset. Checked against the primary sources below on 2026-09-22.

## Establish the boundary

| Download | Governing mechanism |
| --- | --- |
| Binary archive | The packager's explicit files/runtime-assets list. |
| Git source archive | Tracked tree and `export-ignore` attributes. |
| Go module ZIP | Go's module-file rules; export attributes are disabled. |
| Git clone | Git object/history transfer, independent of archive exclusions. |

Inventory tracked file sizes without printing transcript contents. Separate
compressed archive size from uncompressed file totals. Inspect `go:embed`,
`go:generate`, release hooks and runtime file loading before changing exclusions.
Maintain licenses, tests, docs and embedded help/skills/scripts/rules where they
serve the product; a file extension does not determine whether it is required.

For example, these rules exclude one evidence root from Git archives:

```gitattributes
/.specstory export-ignore
/.specstory/** export-ignore
```

Agent plans may have separate roots such as `.claude/plans` or `.codex/plans`.
Target those roots explicitly, keeping settings and skill directories separate.
Retain unrelated attributes, including byte-preservation rules for embedded data.

If smaller **Go module downloads** are also requested, add an empty or
comment-only `go.mod` marker in each existing pure-evidence root. Go treats it as
a nested-module boundary and omits the subtree from the parent's ZIP. Document
why the marker exists; it is not a new installable component. Do not put a
boundary above build inputs, or create unused agent directories solely to hold
markers. Root production dependencies need not change.

Excluding an archive path leaves its Git history public when those commits are
pushed. Publication hygiene still covers the complete newly published commit
range. History migration is a separate operation, not an automatic packaging step.

## Verify independent artifacts

1. Use an exact committed revision. Generate the real source archive, reject
   excluded paths, and extract into a temporary tree with safe path/link handling.
2. Build the actual main package from that tree with the established version
   injection. Run version/help/completion and relevant embedded-resource checks
   using a temporary HOME/XDG environment, not the contributor's live state.
3. Independently create the Go module ZIP using pinned official `x/mod/zip`
   tooling whose Go requirement fits the project. Keep it in a test-only module;
   do not add verifier dependencies to the product module.
4. Run `CheckZip`, inspect entries, `Unzip`, then build/smoke the extracted module.
   Negative fixtures must expose leaked evidence and missing build inputs.
5. After publishing a new version, use a fresh module cache and `GOBIN` to verify
   `go mod download -json`, a fixed-tag install, and `@latest`. A local simulation
   is not proof that a public proxy serves the new version correctly.

### Avoid a false-positive module check

`zip.CreateFromVCS` can internally invoke ordinary `git archive`, which honors
`export-ignore`. The actual Go Git fetcher disables both export attributes, so
that check alone can hide a missing module boundary.

Use a standalone temporary local clone at the candidate SHA. Write Go's exact
override only in **that clone's** `.git/info/attributes`:

```gitattributes
* -export-subst -export-ignore
```

Then run the official ZIP creator/checker against that clone. An ordinary clone
also avoids versions of `CreateFromVCS` that reject linked worktrees. The source
checkout's attributes, refs, index, `go.mod` and `go.sum` stay unchanged. A pinned
`x/mod v0.38.0` fits a Go 1.25 minimum; verify compatibility when changing that pin.

## Evolve the release contract

Keep existing binary asset names, platform coverage, checksum filenames and
provenance flags. For a new dedicated source asset, choose and document its
filename and internal prefix explicitly; rootless archives are useful when a
consumer already expects to build at the extracted root.

GoReleaser's `source` configuration can create the tagged source artifact and
include it in release checksums. A hand-written pipeline may use `git archive`
and its existing checksum step. In either case, verify the actual built artifact,
not just a separate hypothetical archive.

Strict publishers must require the new asset for versions adopting the contract
while retaining the older asset set for older immutable tags. Validate remote
bytes before reporting publication complete. Never add an asset to an already
published immutable release to make an old version satisfy a new contract.
Package managers should continue selecting exact platform filenames, and source
updaters must retain their expected naming, prefix and checksum behavior.

## Sources

- [Git archive attributes](https://git-scm.com/docs/git-archive#ATTRIBUTES).
- [Go module ZIP rules](https://go.dev/ref/mod#zip-files), [Git fetcher implementation](https://go.dev/src/cmd/go/internal/modfetch/codehost/git.go), and [official ZIP API](https://pkg.go.dev/golang.org/x/mod/zip).
- [GoReleaser source archives](https://goreleaser.com/customization/source/).
