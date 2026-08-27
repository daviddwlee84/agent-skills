# Distribution channels, by who actually does the work

A repology page is a map of *other people's* effort as much as your own. Sorting
channels by who acts is what turns "20 packagers" into a two-day job.

## Tier 1 — you control it, automate on tag

| Channel | Mechanism | Notes |
|---|---|---|
| GitHub Releases | GoReleaser / cargo-dist on `push: tags` | The foundation. Everything else consumes these assets. |
| Your Homebrew tap | repo named `homebrew-<x>`, `Formula/*.rb` | `brew install <user>/<x>/<tool>`. No review, no notability bar. |
| Your Scoop bucket | repo with `bucket/*.json` | `scoop bucket add` then `scoop install`. GoReleaser pushes it. |
| `go install` / crates.io | already works | Free, but ships no completions and needs a toolchain. |

Do all of these. They are the only ones you can promise a user.

## Tier 2 — you submit, someone reviews

| Channel | Cost | Gate |
|---|---|---|
| winget-pkgs | PR per release (automatable with `wingetcreate`) | Manifest review; broadest Windows reach |
| AUR | you maintain a PKGBUILD | None really — but it is a maintenance commitment |
| nixpkgs | PR, then ongoing | Reviewer bandwidth |
| homebrew-core | PR | **Notability**: needs real traction; a personal tap does not qualify |
| MacPorts | Portfile PR | Low traffic |

Worth it when: users on that platform are actually asking, and you will still be
around to bump the manifest next release. A stale Tier 2 entry is worse than
none — it installs an old build under your name.

## Tier 3 — they come to you

Debian, Fedora, Alpine, Void, openSUSE, Gentoo, Guix, pkgsrc, FreeBSD ports,
Termux, Spack, Solus, Parabola…

**Do not plan for these.** A distro packager picks up your tool when it is
popular enough to be worth their time. What you *can* do is make it cheap for
them:

- a real OSS license file in the repo root
- semver tags, annotated, with release notes
- reproducible source tarballs (GitHub's auto-tarball is fine)
- no vendored blobs, no network access during build
- a test suite runnable offline
- stable, predictable release-asset names

## Calibration

pueue (~6.3k stars) appears in ~20 repology rows. Its own
`.github/workflows/package-binary.yml` is a tag-triggered cross-compile matrix
that uploads binaries to the GitHub Release — Tier 1, nothing more. Every distro
row is somebody else's volunteer work.

If a tool has fewer than a few thousand stars and someone asks "how do I get into
Debian", the honest answer is: you don't, yet. Ship Tier 1 well.
