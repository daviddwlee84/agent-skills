#!/usr/bin/env bash
# Audit a CLI repo's release/distribution state and report what is missing.
#
# Answers, without you having to look in five places: are there tags with no
# GitHub Release? do the release assets have checksums? has the tap formula or
# scoop manifest fallen behind the latest tag? does the formula install shell
# completions? does cgo force a build matrix?
#
# Usage:
#   check-release-readiness.sh [--repo DIR] [--tag vX.Y.Z]
#                              [--tap OWNER/REPO] [--bucket OWNER/REPO]
#                              [--json]
#
# Flags:
#   --repo DIR         Repository to audit. Default: current directory.
#   --tag vX.Y.Z       Tag to check against. Default: the newest tag.
#   --tap OWNER/REPO   Homebrew tap to compare (e.g. you/homebrew-tap).
#   --bucket OWNER/REPO  Scoop bucket to compare (e.g. you/scoop-bucket).
#   --name NAME        Tool name. Default: the repo directory name.
#   --json             Emit findings as JSON on stdout instead of prose.
#   -h, --help         This message.
#
# Output: findings on stdout (one per line, or a JSON array with --json);
# progress and diagnostics on stderr.
#
# Exit codes:
#   0  ready — no findings
#   1  bad usage
#   2  findings reported (this is the normal "there is work to do" result,
#      not an error)
#   3  a required tool is missing or unauthenticated (git, gh)
set -uo pipefail

REPO="."
TAG=""
TAP=""
BUCKET=""
NAME=""
JSON=0

die() { printf 'check-release-readiness: %s\n' "$1" >&2; exit "${2:-1}"; }
note() { printf '  %s\n' "$1" >&2; }

FINDINGS=()
finding() { FINDINGS+=("$1"); }

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)   REPO="${2:-}"; shift 2 ;;
        --tag)    TAG="${2:-}"; shift 2 ;;
        --tap)    TAP="${2:-}"; shift 2 ;;
        --bucket) BUCKET="${2:-}"; shift 2 ;;
        --name)   NAME="${2:-}"; shift 2 ;;
        --json)   JSON=1; shift ;;
        -h|--help) sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) die "unknown argument: $1" ;;
    esac
done

command -v git >/dev/null 2>&1 || die "git not found" 3
[ -d "$REPO/.git" ] || die "not a git repository: $REPO" 1
cd "$REPO" || die "cannot enter $REPO" 1
[ -n "$NAME" ] || NAME="$(basename "$(pwd)")"

HAVE_GH=0
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    HAVE_GH=1
else
    note "gh missing or unauthenticated — skipping release/tap/bucket checks"
fi

# --- tags -------------------------------------------------------------------
if [ -z "$TAG" ]; then
    TAG="$(git tag -l --sort=-v:refname | head -n1)"
fi
if [ -z "$TAG" ]; then
    finding "no git tags at all — nothing to release from"
else
    note "latest tag: $TAG"
    if [ -z "$(git tag -l --format='%(contents)' "$TAG" | tr -d '[:space:]')" ]; then
        finding "tag $TAG has no annotation; an annotated tag message is the natural release note"
    fi
    ahead="$(git rev-list --count "${TAG}..HEAD" 2>/dev/null || echo 0)"
    [ "$ahead" -gt 0 ] && finding "HEAD is $ahead commits ahead of $TAG — the newest work is unreleased"
fi

# --- goreleaser config ------------------------------------------------------
cfg=""
for f in .goreleaser.yaml .goreleaser.yml; do
    [ -f "$f" ] && cfg="$f" && break
done
if [ -z "$cfg" ]; then
    if [ -f dist-workspace.toml ] || grep -qs 'cargo-dist' Cargo.toml 2>/dev/null; then
        note "cargo-dist project — skipping goreleaser checks"
    else
        finding "no .goreleaser.yaml — releases are manual"
    fi
else
    if command -v goreleaser >/dev/null 2>&1; then
        if ! goreleaser check >/dev/null 2>&1; then
            finding "goreleaser check FAILS on $cfg — a tag push would break"
        fi
    else
        note "goreleaser not installed — cannot validate $cfg"
    fi
    grep -q 'completion' "$cfg" || \
        finding "$cfg has no completion generation — release archives will ship none"
    grep -q 'name_template' "$cfg" || \
        finding "$cfg does not pin archives.name_template — asset names are an API; pin them"
    grep -qE '^\s*brews:' "$cfg" && \
        finding "$cfg uses 'brews:' — deprecated in GoReleaser v2.10; template the formula instead"
fi

# --- release workflow -------------------------------------------------------
if ! ls .github/workflows/*.y*ml >/dev/null 2>&1; then
    finding "no .github/workflows — nothing runs on a tag"
elif ! grep -rqs 'tags:' .github/workflows/; then
    finding "no workflow triggers on tags — releases will not build themselves"
fi

# --- cgo --------------------------------------------------------------------
if [ -f go.mod ] && command -v go >/dev/null 2>&1; then
    if CGO_ENABLED=0 go build -o /dev/null ./... >/dev/null 2>&1; then
        note "CGO_ENABLED=0 builds clean — one Linux runner covers every target"
    else
        finding "CGO_ENABLED=0 build fails — cgo forces a per-OS build matrix, not a single runner"
    fi
fi

# --- GitHub release ---------------------------------------------------------
if [ "$HAVE_GH" = 1 ] && [ -n "$TAG" ]; then
    if ! gh release view "$TAG" >/dev/null 2>&1; then
        finding "tag $TAG has no GitHub Release — users have no binary to download"
    else
        assets="$(gh release view "$TAG" --json assets --jq '.assets[].name' 2>/dev/null)"
        printf '%s\n' "$assets" | grep -qi 'checksum' || \
            finding "release $TAG publishes no checksums file"
        printf '%s\n' "$assets" | grep -qi 'windows' || \
            finding "release $TAG has no windows asset — scoop/winget cannot consume it"
        printf '%s\n' "$assets" | grep -qi 'darwin\|apple' || \
            finding "release $TAG has no darwin asset — a Homebrew formula cannot consume it"
    fi
fi

# --- tap --------------------------------------------------------------------
if [ "$HAVE_GH" = 1 ] && [ -n "$TAP" ]; then
    formula="$(gh api "repos/$TAP/contents/Formula/${NAME}.rb" --jq .content 2>/dev/null | base64 -d 2>/dev/null)"
    if [ -z "$formula" ]; then
        finding "no Formula/${NAME}.rb in $TAP"
    else
        fver="$(printf '%s' "$formula" | sed -n 's/.*version "\([^"]*\)".*/\1/p' | head -n1)"
        [ -z "$fver" ] && fver="$(printf '%s' "$formula" | sed -n 's#.*/archive/refs/tags/v\([^/"]*\)\.tar\.gz.*#\1#p' | head -n1)"
        if [ -n "$fver" ] && [ "v$fver" != "$TAG" ]; then
            finding "tap formula is at $fver but the latest tag is $TAG"
        fi
        printf '%s' "$formula" | grep -q 'generate_completions_from_executable' || \
            finding "tap formula does not install shell completions"
        printf '%s' "$formula" | grep -q 'depends_on "go" => :build' && \
            finding "tap formula still builds from source (depends_on go) — every user downloads a toolchain"
    fi
fi

# --- bucket -----------------------------------------------------------------
if [ "$HAVE_GH" = 1 ] && [ -n "$BUCKET" ]; then
    manifest="$(gh api "repos/$BUCKET/contents/bucket/${NAME}.json" --jq .content 2>/dev/null | base64 -d 2>/dev/null)"
    if [ -z "$manifest" ]; then
        finding "no bucket/${NAME}.json in $BUCKET"
    else
        bver="$(printf '%s' "$manifest" | sed -n 's/.*"version"[: ]*"\([^"]*\)".*/\1/p' | head -n1)"
        if [ -n "$bver" ] && [ "v$bver" != "$TAG" ]; then
            finding "scoop manifest is at $bver but the latest tag is $TAG"
        fi
    fi
fi

# --- report -----------------------------------------------------------------
if [ "$JSON" = 1 ]; then
    printf '['
    for i in "${!FINDINGS[@]}"; do
        [ "$i" -gt 0 ] && printf ','
        printf '%s' "${FINDINGS[$i]}" | sed 's/\\/\\\\/g; s/"/\\"/g; s/^/"/; s/$/"/'
    done
    printf ']\n'
else
    if [ "${#FINDINGS[@]}" -eq 0 ]; then
        printf 'release readiness: OK (no findings)\n'
    else
        printf 'release readiness: %d finding(s)\n' "${#FINDINGS[@]}"
        for f in "${FINDINGS[@]}"; do printf '  - %s\n' "$f"; done
    fi
fi

[ "${#FINDINGS[@]}" -eq 0 ] || exit 2
