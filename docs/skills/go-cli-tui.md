# go-cli-tui

Build Go command-line tools, terminal dashboards, and guided configuration with
Lazygit-inspired interaction: visible state, fast context switching, discoverable
actions, and immediate feedback. The default stack is Cobra plus compatible
Bubble Tea, Bubbles, Lip Gloss, and optional Huh versions.

This is a standalone owned development skill, maintained in
[awesome-lazy-tools](https://github.com/daviddwlee84/awesome-lazy-tools/tree/main/skills/go-cli-tui)
and synced here for distribution under MIT. Edit the canonical source, not this mirror. It contains instructions and ten
references, not a starter application. It primarily serves new tools and new
features, while respecting existing frameworks and public behavior.

## Install and use

```bash
npx skills@latest add daviddwlee84/agent-skills/skills --skill go-cli-tui
```

The grouped picker lists it under **go-cli**. Example requests:

- "Build a Go resource manager with a Lazygit-style list and preview, arrow/Vim
  navigation, and background refresh."
- "Add a guided `hosts add` wizard so users do not need to memorize flags."
- "Improve this Bubble Tea v1 app's focus, search, and refresh behavior without
  changing its framework version."
- "Let agents use this CLI reliably, with bundled operational guidance and
  machine output, then prepare a first `go install` release."
- "Add an upgrade command that updates the running copy and respects source
  builds, published release assets, and package-manager ownership."

For an implementation request, the skill leads through a compact interaction
contract, shared domain operations, implementation, and verification. It does not
stop at recommending a layout.

## Interaction defaults

| Area | Behavior |
|---|---|
| Navigation | Arrows and j/k together; Tab/Shift+Tab for focus; contextual h/l; gg/G for long lists |
| Mouse | Shared pure layout/hit geometry, semantic press/release actions, modal capture, optional native selection |
| Editing | Printable keys stay text; no required normal/insert mode |
| Discoverability | Contextual footer, help, and action menu share effective bindings |
| Continuity | Keep valid selection, filter, and scroll across views, refresh, and wizard return |
| Responsiveness | Initial UI before slow work; reject stale results; distinguish cached, unknown, empty, and failed states |
| Preferences | Optional TOML; XDG on macOS/Linux, native Windows directories; flags → env → file → defaults |

Bare dashboard apps open their UI in a TTY. A designated wizard command such as
`hosts add` guides on bare invocation; ordinary command groups show help.
Partial business flags with missing data produce a usage error. Explicit
`--interactive` starts a prefilled wizard. Global options such as `--config`
alone do not change a bare wizard entry into command mode.

Unknown flags/invalid values report errors before prompting. Non-TTY and JSON
execution never prompt; contradictory interactive/output modes fail clearly.
Wizards retain answers on Back, validate through the shared service, and review
consequential changes before applying them. Prefilled local settings forms can
offer Ctrl+S from any field with optional Review, preserving validation and drafts
on failure; verify raw Ctrl+S and terminal flow control in a real PTY.

## Agent use and staged installation

For tools that need an agent-facing interface, the skill covers embedding one
operational guide in the binary, static offline `--skill`/topic output, JSON
errors, noninteractive authentication behavior, and bounded log streams. CLI,
TUI, and agent calls use the same domain operations. Command help remains the
syntax authority; the guide explains workflow, scope, and uncertain mutation
results. It does not require every tool to ship a skill or skill installer.

An early Go release can start with `go install` using the actual main-package
path, including `/cmd/<name>` when that is the repo layout. Document the Go
requirement and binary `PATH`, recover the installed module version when linker
flags are absent, and verify both a public fixed tag and `@latest` from outside
the checkout. `@latest` does not generally mean the newest main commit.
Prebuilt archives, checksums, and a Homebrew tap can follow when distribution
needs justify them; they are not prerequisites for the first source release.

An explicit upgrade feature selects a strategy from published artifacts and the
running executable's ownership. A source-only release can build an exact tag
with installed Go; published archives need checksum and executable verification;
package-owned copies update through their manager. Build metadata describes
provenance, not who installed the file. A copied Go binary must update at its
resolved current path, independent of today's `GOBIN` or another copy on `PATH`.
Local/dirty builds are preserved by default. Staging, destination locking,
identity rechecks and atomic replacement retain the old file on failure.
Check-only/JSON/read-only behavior and Go toolchain selection are explicit; the
updater does not bootstrap a missing Go command or invoke `sudo`. Embedded
`--skill` content updates with the binary; end users do not run `npx skills` for
that content.

Mouse verification combines state tests with SGR events sent through a real PTY,
including modal capture and stale button presses after resize/target changes.
Monitoring guidance covers timestamped bounded history, source-specific freshness,
real gaps, counter resets and exact drilldowns. Settings editor entry points stay
usable when the file is malformed and retain edits that fail validation.

Maintain a user-facing changelog, pass checks on the exact release source, and
keep changelog version, immutable tag, release notes and installed binary version
consistent. These are completion checks, not a requirement to add packaging.

## Completion and shared operation lessons

Completion setup separates generation, user-file installation, parent-shell
activation and offline candidate queries. Native zsh bridges can query the
current binary; legacy Bash output may need regeneration. Verify actual Tab
input in an isolated shell, not just generated script syntax.

Cross-target and persistent-owner workflows share a reviewed plan between CLI
and TUI. A digest detects stale observations but does not make remote writes
atomic. Keep saved source, owner activation and observed runtime behavior
separate. Background discovery must not replace pending operation surfaces;
after an operation, invalidate affected cached views while retaining stale data.

SSH authentication releases the terminal to native SSH through an explicit
action. Background checks never prompt; configured shared masters and app-owned
fallback sessions have separate lifetimes and cleanup responsibilities.

Standalone shell integration uses a narrow generated environment handoff, preserves
prior values/functions/exit hooks, and keeps authentication outside captured output.
Persistent shell connections have explicit ownership and crash cleanup; generated
container settings identify the actual consumer and preserve existing config owners.
Reverse SSH guidance separates command, shell and service lifetimes, checks the
actual remote bind address, keeps allocated-port stdout separate from diagnostics,
and preserves login-rc precedence with an explicit clean-shell alternative.
Dashboard actions can release the terminal to the same CLI wizard, retain results
until acknowledgement, and refresh the correct target on return. Empty searches and
clipped Apply buttons cannot submit hidden choices.

## References included

| Reference | Load for |
|---|---|
| [Interaction design](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/interaction-design.md) | Layout, focus, dual navigation, filtering, help, Unicode, and resize |
| [CLI, wizards, config](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/cli-wizards-config.md) | Entry policy, form behavior, shared validation, XDG, and precedence |
| [Charm stack](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/charm-stack.md) | Version selection and routing needs to libraries/tools |
| [Async and terminal](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/async-terminal.md) | Generations, cancellation, startup, terminal ownership, and dev-cli lessons |
| [Agent-facing CLI](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/agent-facing-cli.md) | Embedded knowledge, static documentation, machine errors, noninteractive calls, and bounded streams |
| [Go distribution](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/go-distribution.md) | Main-package install paths, version reporting, public tags, and later packaging |
| [Self-update](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/self-update.md) | Conditional source/asset/manager strategies, provenance and ownership, current-copy replacement, and failure preservation |
| [Shell completion](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/shell-completion.md) | Install/status, zsh fpath, offline candidates, update freshness and actual Tab verification |
| [Shell context](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/shell-context.md) | Parent environment, persistent connections, legacy adapters and consumer configuration ownership |
| [Verification](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/references/verification.md) | State tests, real PTY checks, Unicode emulator limits, and three acceptance walkthroughs |

The Charm map includes Glamour, Log, Wish, ANSI/terminal utilities, Harmonica,
Gum, Glow, VHS, and Freeze as optional capabilities. It does not make all of them
dependencies. New code checks current compatible stable releases; existing code
reads its module versions before borrowing examples.

## Sources and limits

[Lazygit](https://github.com/jesseduffield/lazygit/blob/master/AGENTS.md) uses its
own in-tree gocui fork. Its UX is the inspiration; the new-project implementation
preference is [Charm](https://charm.land/). This skill also extracts lessons from
[dev-cli](https://github.com/daviddwlee84/dev-cli), including live filtering,
generation handling, shared wizards, terminal handoffs, embedded skills, and
version reporting, without depending on that project or copying its domain model.

The [external catalog](../catalog/skill-collections.md#go-clitui-candidates)
records the 2026-09-20 comparison of `golang-cli`, `tui-design`, and `bubbletea`,
their manual-install paths, and why this repo chose local integration.

Verification guidance includes deterministic state tests, bad-input/JSON/config
checks, and actual terminal operation. A concrete lazyclash case records pyte
0.8.2's VS16/ZWJ replay limitation and why direct View checks complement PTY
input tests. The three walkthroughs remain specifications, not pre-executed
applications or measured skill benchmarks. Distribution work
can use the optional [CLI release skill](https://github.com/daviddwlee84/agent-skills/tree/main/skills/local/cli-release-distribution).

## Canonical SKILL.md

See [Canonical go-cli-tui/SKILL.md](https://github.com/daviddwlee84/awesome-lazy-tools/blob/main/skills/go-cli-tui/SKILL.md).
