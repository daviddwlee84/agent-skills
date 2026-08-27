# Shell completions that actually reach users

Read this when completions are missing, incomplete, or need wiring into
packaging.

## Two independent failures

Shipping a `completion` subcommand fixes neither on its own.

### 1. The CLI generates completions that complete nothing useful

Cobra and clap both hand you a `completion <shell>` subcommand for free. It knows
your **subcommands** and **flag names**. It does not know flag **values** — those
fall back to filename completion.

Diagnose by asking the binary, using cobra's hidden driver:

```console
$ mytool __complete --to ""
:0
Completion ended with directive: ShellCompDirectiveDefault
```

`:0` is `ShellCompDirectiveDefault` — "shell, do your normal filename thing".
That is the signature of a flag with no completion registered.

Fix (Go / cobra):

```go
_ = root.RegisterFlagCompletionFunc("to",
    func(*cobra.Command, []string, string) ([]string, cobra.ShellCompDirective) {
        // "value\tdescription" — shells that support descriptions render both.
        return []string{"en\tenglish", "ja\tjapanese"}, cobra.ShellCompDirectiveNoFileComp
    })
```

- Always return `ShellCompDirectiveNoFileComp`, or the shell appends filenames to
  your candidates.
- `RegisterFlagCompletionFunc` errors **only** when the flag name doesn't exist,
  and most code ignores that error — so a typo silently degrades to filename
  completion. Cover every registered flag with a test.
- Don't filter by the `toComplete` prefix yourself unless you have a reason; the
  shell filters, and filtering server-side breaks matching on a description.
- The data usually already exists. If the tool has `--json` introspection
  subcommands, those are your completion sources.

`root.ValidArgsFunction = cobra.NoFileCompletions` suppresses filename noise on
positional args — but **not** at the first word, where cobra still offers
subcommand names. That is desirable; don't "fix" it.

### 2. Nothing installs the generated script

`go install` and `cargo install` never install completions. A package manager
won't either unless the packaging says so. This is why a tool can have working
completions on the author's machine (their dotfiles generate them) and none at
all for everyone else.

| Channel | How completions get installed |
|---|---|
| Homebrew formula | `generate_completions_from_executable(bin/"x", shell_parameter_format: :cobra)` |
| Release archives | generate in a GoReleaser `before` hook, add `completions/*` to `archives.files` |
| Scoop / winget | no hook — the user's `$PROFILE` must run the generator (cache it) |
| `go install` / `cargo install` | **never**; document the manual command |
| Distro packages | the packager's job, but only if your archive contains them |

Document the manual path in the README regardless:

```sh
mytool completion zsh  > ~/.zfunc/_mytool                       # dir must be in $fpath
mytool completion bash > ~/.local/share/bash-completion/completions/mytool
mytool completion fish > ~/.config/fish/completions/mytool.fish
mytool completion powershell | Out-String | Invoke-Expression   # add to $PROFILE
```

## Completion must have no side effects

A completion function that calls a config loader which **creates a default config
on first run** means pressing TAB writes files. Use a read-only load path that
falls back to defaults in memory, and test it:

```go
func TestCompletionDoesNotCreateConfig(t *testing.T) {
    dir := t.TempDir()
    t.Setenv("MYTOOL_CONFIG", filepath.Join(dir, "config.toml"))
    runComplete(t, "--provider", "")
    if _, err := os.Stat(filepath.Join(dir, "config.toml")); !os.IsNotExist(err) {
        t.Error("completion created a config file")
    }
}
```

The same rule rules out network calls: TAB must not hit an API.

## Caching generated completions

Regenerating on every shell start costs real milliseconds. The house idiom is a
cache invalidated by the **binary's mtime**, so an upgrade regenerates
automatically:

```sh
[ -f "$cache" ] && [ "$cache" -nt "$(command -v mytool)" ] || \
  mytool completion zsh > "$cache"
```

Write via a temp file and `mv`, so a failing generator never truncates a good
completion file. Never cache empty output — treat it as "retry next time".

## Verifying end to end

1. `mytool __complete --flag ""` lists real candidates (not `:0`).
2. Install from the package manager into a clean environment.
3. The completion file exists where that shell looks for it.
4. A **new** shell (`exec zsh`) completes the flag.

Step 4 matters: zsh caches completions per session, so testing in the shell where
you generated the file proves nothing.
