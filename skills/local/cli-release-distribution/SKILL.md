---
name: cli-release-distribution
description: 'Ship a compiled CLI (Go/Rust) to real users: tag-triggered GoReleaser/cargo-dist cross-compilation, GitHub Releases with checksums, your own Homebrew tap and Scoop bucket, and shell completions that actually get installed. Use when the user says "release my CLI", "publish to Homebrew", "make a tap", "scoop bucket", "winget manifest", "goreleaser", "cross-compile for macOS/Linux/Windows", "prebuilt binaries", "brew install is building from source", "tab completion does not work after install", "how do I get on repology / AUR / nixpkgs", or asks what it takes to distribute a self-authored terminal tool beyond `go install`.'
---

# CLI Release & Distribution

Getting a compiled CLI from "it builds on my machine" to "anyone can install it
in one line, and TAB works". The mechanics are mostly solved; what bites is the
**seams** — the deprecated publisher, the packaging format that quarantines your
binary, the token that can't push, the completion nobody installs.

This skill is the seams. Every claim in `## Gotchas` was paid for once in a real
release.

## When to use

- *"How do I ship prebuilt binaries instead of making people build from source?"*
  → Workflow A.
- *"`brew install` pulls a whole Go toolchain, make it instant"* → Workflow B.
- *"I want Windows users to `scoop install` it"* → Workflow C.
- *"TAB completion does nothing after installing from brew"* → Workflow D. This
  is the most commonly missed piece: package managers do **not** generate
  completions for you.
- *"Do I need docker images or a Mac to cross-compile?"* → almost certainly no;
  see Gotcha 1.
- *"How do I get on repology / AUR / nixpkgs / Debian?"* → read
  `references/channel-tiers.md` first; the honest answer is usually "you don't,
  they come to you."

## When NOT to use

- **Interpreted tools** (Python/Node CLIs). Their distribution is PyPI/npm plus
  `uv tool install` / `npx`, an entirely different problem. Nothing here applies.
- **Libraries.** crates.io / pkg.go.dev publishing needs none of this.
- **GUI apps.** Those genuinely want a signed, notarized Homebrew **cask** — the
  one case where the cask advice this skill argues against is correct.
- **A tool with no users yet.** `go install` / `cargo install` is a fine, honest
  first channel. Set this up when a real person on a real OS can't install it.

## Authoritative sources

| Thing | Where |
|---|---|
| GoReleaser config reference | https://goreleaser.com/customization/ |
| cargo-dist (Rust equivalent) | https://opensource.axo.dev/cargo-dist/ |
| Homebrew Formula API | https://rubydoc.brew.sh/Formula |
| Scoop manifest schema | https://github.com/ScoopInstaller/Scoop/wiki/App-Manifests |
| winget manifest schema | https://github.com/microsoft/winget-pkgs |
| Cross-repo packaging map | https://repology.org/project/<name>/versions |

## Mental model: three tiers of channel

The single most useful reframe. A repology page showing 20 packagers looks like
20 things to do. It isn't — most of them are other people's work.

| Tier | Who acts | Channels | Automate? |
|---|---|---|---|
| **1. Yours** | You, on every tag | GitHub Releases, your own Homebrew tap, your own Scoop bucket, `go install` / crates.io | **Yes — this is the whole job** |
| **2. Submitted** | You open a PR, they review | winget-pkgs, AUR, nixpkgs, homebrew-core, MacPorts | Per release, manually. Mostly gated on notability |
| **3. Downstream** | Volunteers, unprompted | Debian, Fedora, Alpine, Void, Guix, pkgsrc, Termux, Spack | **No. Don't plan for it** |

Reference point: pueue has ~20 repology rows at ~6.3k stars, and its own release
workflow does **Tier 1 only** — a tag-triggered cross-compile matrix that uploads
binaries. Every distro row came from someone else. Make Tier 1 excellent (stable
archive names, checksums, a real license, sane versioning) and Tier 3 becomes
easy for the volunteer who shows up.

Read `references/channel-tiers.md` when the user asks about a specific
distro/packager, or wants to know whether a Tier 2 submission is worth it yet.

## Which channel costs what

Intuition says Windows/Scoop is the hard one. For the **publisher** it is the
opposite — GoReleaser automates Scoop end to end and cannot do Homebrew formulae
at all:

| | Homebrew tap | Scoop bucket |
|---|---|---|
| Repo setup | `gh repo create <user>/homebrew-tap --public` | `gh repo create <user>/scoop-bucket --public` |
| Publishing | **your own template + push script** (`brews:` is deprecated) | a ~10-line `scoops:` block |
| Completions | one line in the formula | no hook — the user's `$PROFILE` must generate them |
| Post-install hooks | rich | minimal |

So: Scoop is *less* work to publish and *thinner* to consume. What genuinely
costs time on Windows is neither of those — it is migrating existing users off a
previous install location (see the PATH-shadowing gotcha), which is your own
history, not Scoop's fault.

## Setup quickstart (Go)

```bash
goreleaser init                 # writes a starter .goreleaser.yaml
goreleaser check                # validate config — do this before every tag
goreleaser release --snapshot --clean   # full local dry run into dist/, no publish
```

`--snapshot` is the highest-value command here: it builds every target and
archive locally, so config mistakes cost seconds instead of a bad tag.

## Workflow A — prebuilt binaries on every tag

1. Confirm you have **no cgo**. `CGO_ENABLED=0 go build` succeeding means one
   Linux runner can build every target. With cgo you need a real matrix — see
   Gotcha 1.
2. Write `.goreleaser.yaml` from `assets/goreleaser.yaml.template`. The parts
   people get wrong: injecting the version via `ldflags -X` (Gotcha 3), and
   generating completions in a `before` hook so they land in the archives.
3. Add the release workflow from `assets/release-workflow.yml.template`,
   triggered on `push: tags: ['v*.*.*']` with `permissions: contents: write`.
4. `goreleaser check && goreleaser release --snapshot --clean`, inspect `dist/`.
5. Tag and push. Verify with `gh release view vX.Y.Z`.

Read `references/goreleaser-config.md` for the annotated config, archive naming,
and the v2 key changes (`formats:`, `directory:`) that break copy-pasted examples.

## Workflow B — your own Homebrew tap

A tap is just a GitHub repo named `homebrew-<name>` with a `Formula/` dir;
`brew install <user>/<name>/<tool>` finds it.

**Publish a formula, not a cask** (Gotcha 2), and generate the formula from a
template in the *tool's* repo rather than hand-editing the tap:

- `packaging/<tool>.rb.tmpl` with `__VERSION__` / `__SHA256_<OS>_<ARCH>__`
  placeholders → `assets/formula.rb.template`.
- `scripts/bump-formula.sh` fills them from `dist/checksums.txt` and pushes.

Read `references/homebrew-tap.md` for the `on_macos`/`on_arm` layout, keeping
`head` support alongside prebuilt bottles, and `brew audit` expectations.

## Workflow C — your own Scoop bucket

A bucket is a GitHub repo with a `bucket/` dir of JSON manifests.

Unlike Homebrew, GoReleaser **can** publish this — a `scoops:` block pushes the
manifest on every tag. Because the manifest is pushed rather than polled, you do
**not** need `checkver`/`autoupdate`; those exist for hand-maintained manifests
that have to discover new upstream versions.

Read `references/scoop-bucket.md` for the manifest shape, `bin`/`shims`
behaviour, and migrating users off a previous install method.

## Workflow D — completions that actually get installed

Two independent failures, and shipping fixes only one:

1. **Your CLI generates no useful completions.** Cobra/clap give you a
   `completion <shell>` subcommand for free — but only for subcommands and flag
   *names*. Flag **values** fall back to filename completion unless you register
   them. Fix with `RegisterFlagCompletionFunc` (Go) / `ValueHint` +
   dynamic completers (clap).
2. **Nothing installs the generated script.** `go install` and `cargo install`
   never will. A package manager won't either unless the packaging says so.

Verify by *asking the binary*, not by eyeballing: `<tool> __complete --flag ""`
prints candidates plus a `:<directive>` line. A bare `:0` means "shell, do your
normal filename thing" — i.e. you have no completion.

Read `references/shell-completions.md` for the per-manager install lines, the
`shell_parameter_format: :cobra` idiom, and the no-side-effects rule.

## Available scripts

### `scripts/check-release-readiness.sh`

Audits a repo before (or after) a release and reports what is missing.

**Flags**: `--repo DIR` (default `.`) · `--tag vX.Y.Z` (default: latest tag) ·
`--tap OWNER/REPO` · `--bucket OWNER/REPO` · `--json` · `--help`

**Checks**: tags without matching GitHub Releases; release assets missing
checksums; a tap formula or bucket manifest whose version lags the latest tag;
`.goreleaser.yaml` presence and `goreleaser check`; whether the formula installs
completions; whether cgo is enabled (i.e. whether a matrix is required).

**Exit codes**: `0` ready · `1` bad usage · `2` findings reported (not an error
— it means there is work to do) · `3` a required tool (`gh`, `git`) is missing
or unauthenticated.

### `scripts/bump-formula.sh`

Renders a formula template from a checksums file and optionally pushes it to a
tap. Generalized from the reference implementation.

**Flags**: `--version VER` (required) · `--template FILE` · `--checksums FILE` ·
`--tap OWNER/REPO` · `--name NAME` · `--out-file FILE` · `--dry-run` · `--help`

**Environment**: `TAP_GITHUB_TOKEN` (push mode only).

**Exit codes**: `0` rendered/pushed · `1` bad usage · `2` a checksum was missing
or a placeholder went unsubstituted · `3` push failed.

## Bundled assets

- `assets/goreleaser.yaml.template` — annotated config: builds, archives,
  checksums, `scoops:`, completion before-hooks.
- `assets/release-workflow.yml.template` — the on-tag GitHub Actions workflow.
- `assets/formula.rb.template` — prebuilt-binary formula with `head` support and
  completion generation.

## Reference files

- `references/channel-tiers.md` — **Read when** the user asks about a specific
  packager (AUR, nixpkgs, winget, Debian…) or wants a distribution roadmap.
- `references/goreleaser-config.md` — **Read when** writing or debugging
  `.goreleaser.yaml`, especially if a copy-pasted example fails `goreleaser check`.
- `references/homebrew-tap.md` — **Read when** creating a tap, converting a
  source-build formula to prebuilt, or `brew install` behaves oddly.
- `references/scoop-bucket.md` — **Read when** setting up Windows distribution
  or migrating Windows users off `go install`.
- `references/shell-completions.md` — **Read when** completions are missing,
  incomplete, or need wiring into packaging.

## See also

- `raycast-extension-dev` — shipping a *Raycast* front-end for the same CLI.
- `git-workflow` — tagging and release-commit conventions.

## Gotchas

- **Pure-Go/pure-Rust means one Linux runner builds everything.** No docker
  images, no macOS/Windows runners, no self-hosted hardware. `CGO_ENABLED=0`
  plus a `goos`/`goarch` list is the entire matrix. cgo (or a `*-sys` crate) is
  what forces real per-OS runners or cross-toolchains. Check before designing
  anything: if `CGO_ENABLED=0 go build ./...` works, you are in the easy case.

- **Cross-compiled macOS binaries are already ad-hoc signed** by the Go linker —
  which is what arm64 requires to execute at all. Verify with `codesign -dv`:
  look for `flags=0x20002(adhoc,linker-signed)`. You do **not** need an Apple
  Developer account to ship a working CLI binary.

- **Homebrew quarantines casks, never formulae.** `grep -rh quarantine
  $(brew --repository)/Library/Homebrew/*.rb` returns only `require
  "cask/quarantine"`. So the notorious *"<app> is damaged and cannot be opened"*
  failure for unsigned prebuilt binaries applies to **casks**. A formula that
  installs a prebuilt binary is fine. Do not let that warning push you into
  build-from-source; it costs every user a full compiler toolchain.

- **GoReleaser can no longer publish a Homebrew formula.** `brews:` was
  deprecated in v2.10 in favour of `homebrew_casks:` — which is the format you
  must avoid, per the previous gotcha. Template the formula and push it yourself
  (Workflow B). GoReleaser still handles Scoop fine.

- **`-X` against a build-info field is a silent no-op.** In Go,
  `debug.ReadBuildInfo().Main.Version` is *not* a linker symbol. Point `ldflags
  -X` at your own `var version string` and fall back to build info. The failure
  mode is nasty: the build succeeds and the binary reports `(devel)`.

- **`GITHUB_TOKEN` cannot push to another repo.** Publishing to a tap or bucket
  needs a fine-grained PAT with `contents: write` on **each** target repo, stored
  as a secret. The default workflow token is scoped to its own repository. And
  **`gh` cannot mint the PAT** — GitHub removed the API (`POST /authorizations`
  404s), so creating it is browser-only at
  <https://github.com/settings/personal-access-tokens/new>. Everything after that
  is scriptable: `gh secret set TAP_GITHUB_TOKEN --repo OWNER/TOOL`. Don't burn
  time looking for a `gh` subcommand that does not exist.

- **Moving a tool from `go install` to a package manager leaves a shadow.** The
  old binary sits in `~/.local/bin` (or `~\.local\bin`), which typically precedes
  the package manager's bin/shims dir on PATH. `brew upgrade` / `scoop update`
  then report success while the old build keeps running. Delete the old copy in
  the migration — but **only after** verifying the new one exists, so a failed
  install never leaves the user with nothing. `command -v -a <tool>` /
  `Get-Command <tool> -All` is the diagnostic.

- **Completion generation must have no side effects.** If a completion function
  calls a config loader that creates a default config on first run, then pressing
  TAB writes files. Use a read-only path, and test it: run the completion in a
  temp `HOME` and assert nothing was created.

- **Archive naming is an API.** Downstream packagers, `.chezmoiexternal` URLs and
  install scripts hard-code your asset names. Pin `name_template` explicitly
  rather than inheriting a default that can change between GoReleaser versions.
  Note the default strips the leading `v`: tag `v0.6.0` → `tool_0.6.0_darwin_arm64.tar.gz`.

- **Test the release config in CI, not at tag time.** Add `goreleaser check` to
  the normal PR workflow. A broken config discovered by a tag push means either
  deleting a public tag or shipping a fix release.
