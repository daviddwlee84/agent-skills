# Bring `raycast-extension-dev` up to date: cross-platform + AI Extensions

## Context

`skills/local/raycast-extension-dev` was written against a macOS-only, Pro-gated
picture of Raycast that is no longer true. Two independent gaps:

1. **Cross-platform.** Raycast for Windows shipped, and `platforms` landed in the
   manifest in **1.103.0 (2025-09-15)**. The skill declares itself macOS-only in
   its opening paragraph (`SKILL.md:18-19`) and hardcodes `platforms: ["macOS"]`
   in the scaffolder template, the store checklist, and the readiness script — so
   every extension it produces is silently Windows-invisible, and it teaches none
   of the per-platform mechanisms (shortcuts, preference defaults, `windowsAppId`,
   `runPowerShellScript`).

2. **AI Extensions.** The skill tells the agent to *deprioritise* AI tools on two
   grounds, one of which is **factually wrong**:
   - `SKILL.md:45-46` / `manifest-and-commands.md:268-270`: *"there is no
     `confirmAlert` equivalent inside a tool call, so a first version must be
     read-only."* — `Tool.Confirmation<Input>` exists and is documented.
   - *"Pro-gated, so they can never be the primary UX"* — access also comes from
     the free message allowance, Custom Providers (`providers.yaml`, e.g. GitHub
     Copilot) and local Ollama models. The docs page still says Pro; reality has
     moved. The only correct rule is the runtime gate `environment.canAccess(AI)`.
   - `ai.instructions` / `ai.evals` / `ai.yaml` / `npx ray evals` are absent
     entirely — and `ai.evals` is what renders the **Suggested Prompts** list
     under `@extension` in Quick AI.

Outcome: an agent using this skill should treat macOS as a *default*, not a
premise; should reach for `platforms: ["macOS", "Windows"]` whenever nothing
platform-specific is used; and should propose an AI tool layer (with confirmation
and suggested prompts) for any extension whose transport already returns
structured data.

## Verified facts — the source of truth for this rewrite

All confirmed against live docs on 2026-07-28. **Do not re-derive from memory.**

### Cross-platform

| Fact | Source wording |
|---|---|
| `platforms` values | `"macOS"` or `"Windows"` |
| Default when omitted | *"By default, if not specified, the field's value is `["macOS"]`"* (changelog 1.103.0, 2025-09-15) |
| Scope | **extension-level only** — no per-command `platforms` |
| Per-platform values | *"you can specify a different value per platform by passing an object: `{ "macOS": ..., "Windows": ... }`"* — applies to preference `default` |
| Per-platform shortcuts | changelog **1.98.0 (2025-05-08)**; `{ macOS: { modifiers: ["cmd","shift"], key: "c" }, Windows: { modifiers: ["ctrl","shift"], key: "c" } }` |
| Hardcoded modifier | *"If you use shortcuts and specify a modifier like `cmd`, the shortcut will be ignored on Windows (and vice-versa…)"* — **silent**, no lint error |
| Menu bar | *"Menubar commands aren't available on Windows."* |
| Scripts | `runPowerShellScript` — *"Only available on Windows"*; `runAppleScript` is macOS-only |
| Applications | `Application` carries both `bundleId` (*"The macOS bundle identifier"*) and `windowsAppId` (*"The Windows App ID"*) |
| Store guidance | *"if you use platform-specific APIs, restrict the `platforms` field to the corresponding platform"* |
| Porting | *"All extensions that do not require native code will work out of the box on both platforms."* (raycast.com/windows) |
| Requirements | Raycast ≥ 1.26.0, Node ≥ 22.14, npm ≥ 7; Windows 10 21H2+ / Windows 11 |

**Undocumented — write as unverified, do not assert:** whether AI Extensions,
Browser Extension API, or Window Management API work on Windows. Neither the
changelog nor raycast.com/windows lists them as unavailable.

### AI Extensions

| Fact | Source wording |
|---|---|
| `tools[]` fields | `name` (*"directly maps to the entry point file"*), `title`, `description`, `icon` |
| Tool signature | *"A tool expects a single object as its input"*; `export default function tool(input: Input)` |
| Parameter schema | JSDoc on the `Input` type — *"add descriptions as JSDoc comments"* |
| Confirmation | `type Confirmation<T> = (input: T) => Promise<undefined \| {...}>`; `export const confirmation: Tool.Confirmation<Input> = (input) => {`; returns `message`, `info[]` (`{name, value}`), `style` (regular/destructive), `image`; `undefined` skips it; *"called before the actual tool is executed"* |
| `ai.instructions` | *"added as a system message whenever the extension is mentioned"* |
| `ai.evals` | *"Evals are a way to test your AI extension. Think of them as integrations tests."* |
| **Suggested Prompts** | *"They are also used as suggested prompts for the user to learn how to make the most out of your AI Extension."* — `usedAsExample` defaults to `true` |
| File location | *"we recommend you to use a `ai.yaml` file in the root of your extension next to the `package.json`"* |
| Runner | `npx ray evals`; matcher shown: `callsTool` |
| Access gate | *"You can check if a user has access to the API using `environment.canAccess(AI)`"* / *"If the user doesn't wish to get access, the API call will throw an error."* |
| Stale doc to cite as stale | ai/getting-started: *"To use AI APIs or AI Extensions, you need to subscribe to Raycast Pro."* — contradicted by the free allowance, Custom Providers and Ollama Local Models in Raycast Settings → AI |

## Changes

### 1. `SKILL.md`

- **Frontmatter `description`** — add trigger terms: Windows, cross-platform,
  `platforms`, `runPowerShellScript`, AI extension, `tools[]`, `ai.evals`,
  suggested prompts. Keep it single-quoted YAML; double any internal apostrophe.
  (`make lint-frontmatter` exists precisely because this broke before.)
- **Replace the `macOS only.` paragraph (`:18-19`)** with the three-layer model:
  Raycast UI fully shared → domain/API logic shared → OS adapter split. State
  that `platforms` defaults to `["macOS"]` when omitted, so *not deciding* is a
  decision that hides the extension from the Windows store.
- **Surface map (`:88-94`)** — add a `Platform` column. `menu-bar` → macOS only
  (confirmed). AI tools → `platforms` availability undocumented.
- **`When NOT to use` (`:44-48`)** — delete the "Pro-gated / must be read-only"
  bullet. Replace with a pointer to Workflow G.
- **New `Workflow G — add an AI tool layer`**, sized like the existing workflows:
  `tools[]` entry → `src/tools/<name>.ts` with a JSDoc'd `Input` → `confirmation`
  for anything mutating → `ai.yaml` with `instructions` + `evals` → `npx ray evals`.
  Make the reuse point explicit: if Workflow B's transport already returns
  structured data, a tool is a thin wrapper and the work is prompt-shaped.
- **Workflow F checklist (`:295`)** — `platforms` line becomes a decision, plus a
  line for `ai.evals` when `tools[]` exists.
- **Reference table + See also** — register the two new reference files.
- **Gotchas** — add: silent `cmd`-on-Windows shortcut drop; `platforms` defaulting
  to macOS; `platforms` being extension-level so a menu-bar command forces the
  whole extension to macOS; `Tool.Confirmation` existing (worded as a correction);
  `environment.canAccess(AI)` being the gate rather than a subscription check.

### 2. New `references/cross-platform.md`

Read-it-when: *targeting Windows, seeing a shortcut do nothing on one OS, or
shelling out to a platform-specific script.* Sections: the `platforms` field and
its default · the three-layer split with a `src/platform/{macos,windows}.ts`
layout and a `process.platform === "win32"` seam · `runAppleScript` vs
`runPowerShellScript` · per-platform shortcut objects · per-platform preference
`default` objects · `bundleId` vs `windowsAppId` and path shapes · a
what-works-where table that marks the undocumented rows **unverified** rather
than guessing · which existing gotchas are macOS-scoped (launchd `PATH`,
Homebrew prefixes, `sips`) and what the Windows equivalent question is.

### 3. New `references/ai-extensions.md`

Read-it-when: *adding `tools[]`, writing `ai.yaml`, or the user asks why the
`@extension` prompt list is empty.* Sections: access model (the three funding
paths + `environment.canAccess(AI)` + the stale Pro sentence, cited and dated) ·
`tools[]` and the file mapping · `Input` + JSDoc as the parameter schema ·
`Tool.Confirmation` with a destructive example · `ai.yaml` with `instructions`
and `evals` · **evals *are* the Suggested Prompts** (`usedAsExample`), with a
worked example matching the screenshot shape (a read-only overview prompt, a
"what's running" prompt, a diagnostic prompt that explicitly says *don't fix
anything*) · `npx ray evals` and why it is a manual step, not a gate step.

### 4. Existing references

- `manifest-and-commands.md:31` — `platforms` in the example becomes a decision
  with both values shown; `:40` reworded from "mandatory" to the real rule.
  `:259-273` AI tools section shrinks to a pointer at `ai-extensions.md`, with
  the two wrong sentences removed.
- `ui-patterns.md` — `Keyboard.Shortcut.Common.*` table gains a **Windows**
  column; add the per-platform shortcut object and the silent-drop warning next
  to the existing reserved-shortcut tables.
- `menu-bar.md:36-37` — note that this forces the *whole extension* to
  `["macOS"]`, since `platforms` has no per-command form.
- `store-publishing.md:39` — same checklist change as `SKILL.md:295`.

### 5. Assets

- `package.json.template` — `"platforms": __PLATFORMS__` and a `__TOOLS__`
  splice marker. **Omit `tools` entirely when there are none** (not `[]`).
- New `assets/tool.ts.template` — JSDoc'd `Input`, default-exported tool,
  commented-out `confirmation` export ready to uncomment.
- New `assets/ai.yaml.template` — `instructions` + three `evals` entries.
- Register both in the bundled-assets table in `SKILL.md`.

### 6. `scripts/new-raycast-extension.sh`

Add `--platforms LIST` (comma-separated, validated against `macOS|Windows`,
default `macOS`) and repeatable `--tool NAME[:TITLE]`. Reuse the existing awk
splice at `:200-211` that already handles `__COMMANDS__` — same mechanism for
`__TOOLS__` and `__PLATFORMS__`. Writes `src/tools/<name>.ts` per tool and one
`ai.yaml` when any tool exists. Reject at parse time (exit 1): a `menu-bar`
command combined with `Windows` in `--platforms`; a tool name that is not
kebab-case. Update `usage()`, the `--json` output, and the flag list in
`SKILL.md:331-336`.

### 7. `scripts/check-store-readiness.sh`

Bump `VERSION` to `1.1.0`. Keep the `record id status detail fix` contract, the
JSON stdout shape, and the 0/1/2/3/4 exit codes unchanged.

| id | status | condition |
|---|---|---|
| `platforms-menu-bar-exclusive` | fail | a `menu-bar` command exists **and** `platforms` includes `Windows` — or `platforms` is set and omits `macOS`. Absent `platforms` = `["macOS"]` = pass. Replaces `platforms-macos-when-menu-bar` (`:153-160`). |
| `platforms-windows-macos-apis` | fail | `platforms` includes `Windows` **and** `src/` greps `runAppleScript`, `MenuBarExtra`, or a literal `/opt/homebrew` / `/usr/local/bin` |
| `shortcuts-hardcoded-cmd` | warn | `platforms` includes `Windows` and `src/` has a `modifiers:` array containing `"cmd"` with no sibling `Windows:` key |
| `ai-evals-present` | warn | `tools[]` non-empty and neither `ai.yaml` nor `package.json` declares `evals` — i.e. no Suggested Prompts |
| `ai-tool-confirmation` | warn | `tools[]` non-empty and no `export const confirmation` anywhere under `src/tools/` |

Use `grep` for the YAML probe — do **not** add a `yq` dependency, since exit code
3 is reserved for "a required tool is missing, so a check was skipped" and a
missing `yq` would wrongly poison the run. Follow the existing
`no-handwritten-preferences` grep heuristic for style.

## Verification

```bash
S=skills/local/raycast-extension-dev

# 1. Script contracts
bash $S/scripts/new-raycast-extension.sh --help
bash $S/scripts/check-store-readiness.sh --help
bash $S/scripts/new-raycast-extension.sh --dry-run --json --dir /tmp/x --name x \
  --platforms macOS,Windows --command tasks:view --tool list-tasks

# 2. Negative arg cases must exit 1
bash $S/scripts/new-raycast-extension.sh --dry-run --dir /tmp/y --name y \
  --platforms macOS,Windows --command menu:menu-bar   # menu-bar + Windows
bash $S/scripts/new-raycast-extension.sh --dry-run --dir /tmp/y --name y \
  --platforms Linux                                    # bad platform

# 3. The real check — generated manifests must satisfy the LIVE Raycast schema
bash $S/scripts/new-raycast-extension.sh --dir /tmp/rc-x --name rc-x \
  --author "$USER" --platforms macOS,Windows --command tasks:view --tool list-tasks
cd /tmp/rc-x && npm install && npm run build && npx tsc --noEmit && CI=true npx ray lint
```

`ray lint` validating a `platforms: ["macOS","Windows"]` + `tools[]` +
`ai.yaml` scaffold is the strongest available proof that the new template shapes
are correct — it validates against the published extension schema, and `CI=true`
turns on the extra checks (per the existing gotcha at `SKILL.md:460-470`).

```bash
# 4. Readiness checks fire — positive and negative fixtures
bash $S/scripts/check-store-readiness.sh /tmp/rc-x --json | \
  node -e 'JSON.parse(require("fs").readFileSync(0)).forEach(c=>console.log(c.status,c.id))'
# assert all five new ids appear; then hand-edit /tmp/rc-x/package.json to add a
# menu-bar command and confirm platforms-menu-bar-exclusive fails with exit 4

# 5. Repo gates (CLAUDE.md)
make lint-frontmatter && make validate
```

Manual, cannot be automated here: `npx ray evals` needs AI access plus network,
and confirming the Suggested Prompts render requires opening `@rc-x` in Raycast.
Note both in the skill as manual steps rather than adding them to the gate.

No `marketplace.json` or `vendor.yaml` change — the skill is already registered
and is local, not vendored. No new symlink under `.agents/skills/` — per
CLAUDE.md this skill is downstream-only.

## Out of scope

- Asserting Windows availability for AI Extensions, Browser Extension API, or
  Window Management API. Undocumented in both the changelog and
  raycast.com/windows; the reference will say so explicitly instead of guessing.
- Actually porting any real extension to Windows.
- A `just evals` recipe — it needs credentials and network, so it does not belong
  in a gate that must run offline.
