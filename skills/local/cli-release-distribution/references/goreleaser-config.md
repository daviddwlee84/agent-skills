# .goreleaser.yaml, annotated

Read this when writing or debugging the config, especially if a copy-pasted
example fails `goreleaser check`.

## The v2 key changes that break old examples

Most GoReleaser snippets online are v1. These renames are the usual cause of a
config that "worked in the blog post":

| v1 | v2 | Where |
|---|---|---|
| `format: tar.gz` | `formats: [tar.gz]` | `archives` (and `format_overrides`) |
| `folder:` | `directory:` | `scoops`, `nfpms` |
| `replacements:` | *removed* | `archives` — use `name_template` |
| `brews:` | `homebrew_casks:` | **deprecated in v2.10 — see homebrew-tap.md; do not migrate** |

Always start with `goreleaser check`. It validates keys against the installed
version, which beats guessing.

## Skeleton

```yaml
version: 2
project_name: mytool

before:
  hooks:
    - go mod download
    # Completions are generated here so they can be archived. Nothing else
    # will produce them, and no package manager generates them for you.
    - sh -c 'mkdir -p completions'
    - sh -c 'go run . completion bash       > completions/mytool.bash'
    - sh -c 'go run . completion zsh        > completions/mytool.zsh'
    - sh -c 'go run . completion fish       > completions/mytool.fish'
    - sh -c 'go run . completion powershell > completions/mytool.ps1'

builds:
  - id: mytool
    env: [CGO_ENABLED=0]          # the reason one Linux runner suffices
    goos: [darwin, linux, windows]
    goarch: [amd64, arm64]
    ldflags:
      # Point -X at your own `var version string`, never at a build-info field.
      - -s -w -X github.com/you/mytool/cmd.version={{ .Tag }}

archives:
  - id: default
    # Pin this. Downstream packagers hard-code asset names.
    name_template: "{{ .ProjectName }}_{{ .Version }}_{{ .Os }}_{{ .Arch }}"
    formats: [tar.gz]
    format_overrides:
      - goos: windows
        formats: [zip]
    files:
      - LICENSE
      - README.md
      - completions/*

checksum:
  name_template: checksums.txt

scoops:
  - name: mytool
    repository:
      owner: you
      name: scoop-bucket
      branch: main
      token: "{{ .Env.TAP_GITHUB_TOKEN }}"   # NOT the default GITHUB_TOKEN
    directory: bucket
    homepage: https://github.com/you/mytool
    description: What it does
    license: MIT

changelog:
  use: git
  sort: asc
  filters:
    exclude: ['^docs:', '^chore:', '^test:']
```

## Version templating

- `{{ .Tag }}` → `v0.6.0` (with the `v`)
- `{{ .Version }}` → `0.6.0` (stripped)

Archive names use `.Version`, so tag `v0.6.0` produces
`mytool_0.6.0_darwin_arm64.tar.gz`. Homebrew's `version` field is also the
stripped form — which is why a formula that tests `assert_match "v#{version}"`
has to re-add the `v`. Get this wrong and the release publishes with URLs that
404.

Inject `{{ .Tag }}` into `ldflags` (not `.Version`) if your `--version` output is
expected to carry the `v`.

## Release notes

By default GoReleaser builds a changelog from commits. To use an annotated tag's
message instead:

```bash
notes="$(git tag -l --format='%(contents)' "$GITHUB_REF_NAME")"
[ -n "$(printf '%s' "$notes" | tr -d '[:space:]')" ] && \
  echo "RELEASE_NOTES_ARG=--release-notes=$RUNNER_TEMP/notes.md" >> "$GITHUB_ENV"
```

Falling back to the commit changelog when the tag has no body keeps a plain
`git tag vX.Y.Z` from producing an empty release.

## Local verification

```bash
goreleaser check                        # config valid for THIS version
goreleaser release --snapshot --clean   # build everything, publish nothing
tar tzf dist/mytool_*_darwin_arm64.tar.gz   # completions/ really in there?
codesign -dv <extracted binary>             # adhoc,linker-signed on darwin
```

A snapshot builds all targets; on a laptop that is minutes, not seconds. Budget
for it before tagging.

## Rust

cargo-dist covers the same ground (`dist init`, `dist plan`, `dist build`) and
does generate Homebrew formulae — it never adopted the cask migration, so the
Homebrew workaround in this skill is Go-specific. The cross-compilation,
checksum, completion and PAT gotchas all still apply.
