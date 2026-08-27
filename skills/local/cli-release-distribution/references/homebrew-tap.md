# Your own Homebrew tap

Read this when creating a tap, converting a source-build formula to prebuilt, or
when `brew install` behaves unexpectedly.

## What a tap is

A GitHub repo named `homebrew-<name>` containing `Formula/*.rb`. Then
`brew install <user>/<name>/<tool>` works — the middle segment drops the
`homebrew-` prefix. No review process, no notability bar, no relationship with
homebrew-core.

## Formula, not cask — the decision that matters

| | Formula | Cask |
|---|---|---|
| For | CLI tools, libraries | GUI apps, big vendor binaries |
| Quarantine applied? | **No** | **Yes** |
| Unsigned prebuilt binary | works | *"<app> is damaged and cannot be opened"* |
| GoReleaser support | dropped in v2.10 | `homebrew_casks:` |

Verify the quarantine claim yourself:

```console
$ grep -rh quarantine $(brew --repository)/Library/Homebrew/*.rb
require "cask/quarantine"
...
```

Every hit is under `cask/`. Homebrew never quarantines formula-installed files.

This matters because the obvious migration path — GoReleaser deprecated `brews:`,
so switch to `homebrew_casks:` — lands you on the broken combination: an unsigned
prebuilt binary in the one format that gets quarantined. Publish a formula and
push it yourself instead.

## Prebuilt formula shape

```ruby
class Mytool < Formula
  desc "..."
  homepage "https://github.com/you/mytool"
  version "0.6.0"          # no leading "v"
  license "MIT"

  on_macos do
    on_arm  { url ".../v0.6.0/mytool_0.6.0_darwin_arm64.tar.gz"; sha256 "..." }
    on_intel{ url ".../v0.6.0/mytool_0.6.0_darwin_amd64.tar.gz"; sha256 "..." }
  end
  on_linux do
    on_arm  { url ".../v0.6.0/mytool_0.6.0_linux_arm64.tar.gz";  sha256 "..." }
    on_intel{ url ".../v0.6.0/mytool_0.6.0_linux_amd64.tar.gz";  sha256 "..." }
  end

  # Keep `brew install --HEAD` working; the build dep applies only to that path.
  head do
    url "https://github.com/you/mytool.git", branch: "main"
    depends_on "go" => :build
  end

  def install
    if build.head?
      system "go", "build", *std_go_args(ldflags: "-s -w")
    else
      bin.install "mytool"
    end
    generate_completions_from_executable(bin/"mytool", shell_parameter_format: :cobra)
  end

  test do
    assert_match "v#{version}", shell_output("#{bin}/mytool --version")
  end
end
```

Notes:

- `version` is the **stripped** form; re-add the `v` in URLs and in a `--version`
  assertion.
- `generate_completions_from_executable` with `shell_parameter_format: :cobra`
  runs `<binary> completion <shell>`. Other formats: `:clap`, `:click`, `:go`,
  or pass explicit args (`generate_completions_from_executable(bin/"x",
  "completions", shells: [:bash, :zsh])`).
- Dropping `depends_on "go" => :build` from the non-head path is the whole point:
  it stops every user downloading a compiler toolchain.

## Generate the formula; don't hand-edit the tap

Keep `packaging/<tool>.rb.tmpl` in the **tool's** repo with `__VERSION__` and
`__SHA256_<OS>_<ARCH>__` placeholders, and have the release workflow render and
push it. Benefits: the formula is reviewed alongside the code that changes it,
and a hand edit can never silently diverge.

State it loudly in the tap's README and in the tool's AGENTS.md: *the formula is
generated; edits here are overwritten by the next release.*

## Verification

```bash
brew update && brew install <user>/<tap>/<tool>
brew audit --strict --online <user>/<tap>/<tool>
brew test <user>/<tap>/<tool>
ls "$(brew --prefix)/share/zsh/site-functions/_<tool>"   # completions landed?
```

`brew audit --strict` will grumble about prebuilt binaries in a formula. In a
personal tap that is advisory, not fatal — homebrew-core's rules do not apply.

## Gotchas

- **Homebrew 6.0 added a tap-trust gate.** A newly tapped third-party repo can be
  `Untrusted`, and installs fail with *"Refusing to load formula ... from
  untrusted tap"*. Automation must `brew tap-info <tap>` and `brew trust <tap>`
  before `brew bundle` / ansible installs. Tools that only tap (e.g. ansible's
  `homebrew_tap`) have no trust parameter and will leave you stuck.
- **The tap needs its own PAT.** See the token gotcha in SKILL.md.
- **Linux users get the formula too.** Homebrew on Linux is real; include
  `linux_amd64`/`linux_arm64` URLs or wrap the macOS blocks so a Linux install
  fails clearly rather than mysteriously.
