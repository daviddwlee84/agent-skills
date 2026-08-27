# Your own Scoop bucket (Windows)

Read this when setting up Windows distribution, or migrating Windows users off
`go install` / a source build.

## What a bucket is

A GitHub repo with a `bucket/` directory of JSON manifests:

```powershell
scoop bucket add mybucket https://github.com/you/scoop-bucket
scoop install mybucket/mytool
```

No review, no submission. The bucket-qualified name (`mybucket/mytool`) is worth
using in automation — it disambiguates from a same-named app in `main`.

## GoReleaser publishes it for you

Unlike Homebrew formulae, Scoop is fully supported. A `scoops:` block pushes
`bucket/mytool.json` on every tag:

```yaml
scoops:
  - name: mytool
    repository:
      owner: you
      name: scoop-bucket
      branch: main
      token: "{{ .Env.TAP_GITHUB_TOKEN }}"
    directory: bucket
    homepage: https://github.com/you/mytool
    description: What it does
    license: MIT
```

Generated manifest:

```json
{
    "version": "0.6.0",
    "architecture": {
        "64bit": { "url": "...windows_amd64.zip", "bin": ["mytool.exe"], "hash": "..." },
        "arm64": { "url": "...windows_arm64.zip", "bin": ["mytool.exe"], "hash": "..." }
    },
    "homepage": "...", "license": "MIT", "description": "..."
}
```

## You do NOT need `checkver` / `autoupdate`

Those exist so a **hand-maintained** manifest can discover new upstream versions
by scraping a page and guessing a URL. When GoReleaser pushes the manifest, the
version and hashes are exact and already correct. Adding `checkver` on top just
creates a second, worse source of truth.

Corollary: **never hand-edit `bucket/*.json`.** The next release overwrites it.
Say so in the bucket's README.

## Migrating users off a previous install method

The trap that costs the most time. If the tool was previously installed to a
general user bin dir (`~\.local\bin`, `%USERPROFILE%\go\bin`), that dir usually
precedes `~\scoop\shims` on `PATH`. Both binaries then exist and the **old** one
wins — `scoop update` reports success while the version never changes.

Diagnose:

```powershell
Get-Command mytool -All | Select-Object -ExpandProperty Source
```

Fix, in automation:

```powershell
$old = Join-Path $HOME '.local\bin\mytool.exe'
if (Test-Path -LiteralPath $old) {
    $scoopRoot = if ($env:SCOOP) { $env:SCOOP } else { Join-Path $HOME 'scoop' }
    if (Test-Path -LiteralPath (Join-Path $scoopRoot 'shims\mytool.exe')) {
        Remove-Item -LiteralPath $old -Force -ErrorAction SilentlyContinue
    }
}
```

The nested check is the important part: **only delete the old binary once the
shim exists**, so a failed or skipped install never leaves the machine with no
tool at all. Honour `$env:SCOOP` — the root is not always `~\scoop`.

## Completions on Windows

Scoop has no completion hook. PowerShell completions are loaded from the user's
`$PROFILE`, typically by running the generator and caching the output:

```powershell
mytool completion powershell | Out-String | Invoke-Expression
```

Cache it against the binary's `LastWriteTimeUtc` so an upgrade regenerates
automatically and shell startup stays fast. See `shell-completions.md`.

## winget as a Tier 2 follow-up

Broader reach, but every release needs a PR to `microsoft/winget-pkgs` and a
review. `wingetcreate update <Id> --version X.Y.Z --urls ... --submit` automates
most of it. Do this only once the Scoop path works and someone actually asks.
